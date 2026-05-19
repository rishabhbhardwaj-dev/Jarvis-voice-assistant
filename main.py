"""
JARVIS AI — main.py v3.0
Always-on wake word detection system.

Voice flow:
  [IDLE]  → always listening for "Hey Jarvis" / "Jarvis"
  [WAKE]  → wake word detected → says "Yes, Sir?"
  [CMD]   → listens for actual command (8 sec window)
  [PROC]  → processes command via Claude / system handler
  [IDLE]  → loops back

Special voice commands:
  "Jarvis quit" / "shutdown Jarvis"  → exits the process
  "Jarvis restart" / "restart Jarvis" → hot-restarts the process
  "Jarvis sleep"                      → pauses wake-word listening
  "wake up Jarvis"                    → resumes from sleep
"""

import speech_recognition as sr
import os
import sys
import webbrowser
import datetime
import subprocess
import threading
import time
import random
import queue
import json
import base64
import io
import logging
import psutil
from flask import Flask, jsonify, request, send_from_directory, Response
from flask_cors import CORS
from groq import Groq
from config import groq_api_key

# ─────────────────────────────────────────
#  Logging — Professional output
# ─────────────────────────────────────────
# Force UTF-8 on Windows terminals to handle emoji/unicode
import io as _io
_utf8_stdout = _io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
_handler = logging.StreamHandler(_utf8_stdout)
_handler.setFormatter(logging.Formatter(
    fmt="%(asctime)s  [%(levelname)s]  %(message)s",
    datefmt="%H:%M:%S"
))
logging.basicConfig(level=logging.INFO, handlers=[_handler])
log = logging.getLogger("JARVIS")

# ─────────────────────────────────────────
#  Flask Setup
# ─────────────────────────────────────────
app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

# ─────────────────────────────────────────
#  SSE — Server-Sent Events broadcast
# ─────────────────────────────────────────
sse_subscribers = []   # list of queue.Queue, one per connected browser tab
_current_state  = {"status": "WAITING", "message": "Say 'Hey Jarvis' to activate...", "color": "dim"}

def broadcast(event_type: str, data: dict):
    """Push a JSON event to every connected SSE client."""
    global _current_state
    if event_type == "state":
        _current_state = data   # always remember last state
    payload = json.dumps({"type": event_type, "data": data})
    dead = []
    for q in sse_subscribers:
        try:
            q.put_nowait(payload)
        except queue.Full:
            dead.append(q)
    for q in dead:
        sse_subscribers.remove(q)

# ─────────────────────────────────────────
#  Groq AI — Setup & Chat History
# ─────────────────────────────────────────
_groq_client = Groq(api_key=groq_api_key)
GROQ_MODEL       = "llama-3.3-70b-versatile"
GROQ_VISION_MODEL = "meta-llama/llama-4-scout-17b-16e-instruct"

chat_history = []   # multi-turn: [{"role": "user"|"assistant", "content": str}]
chat_str     = ""
SAVES_DIR    = os.path.join(os.path.dirname(__file__), "JarvisAI_Saves")

SYSTEM_PROMPT = (
    "You are Jarvis, a smart, witty, and highly capable AI desktop assistant. "
    "Keep answers VERY concise, brief, and friendly (maximum 1-2 sentences unless specifically asked for more detail). "
    "Maintain a high-tech persona inspired by Tony Stark's JARVIS. "
    "When asked to open apps or websites, confirm you are doing so. "
    "Address the user as 'Sir'. Never start responses with 'Sir' as the very first word."
)

# ─────────────────────────────────────────
#  TTS — Windows PowerShell (interruptible)
# ─────────────────────────────────────────
import unicodedata as _ud

# Global TTS process tracker — allows barge-in / interrupt
_tts_proc: subprocess.Popen | None = None
_tts_lock = threading.Lock()


def _tts_sanitize(text: str) -> str:
    """Convert to ASCII and strip PowerShell-unsafe characters."""
    # Normalize Unicode (e.g. curly quotes ’ ‘ “ ” …) to ASCII equivalents
    normalized = _ud.normalize('NFKD', text)
    ascii_only = normalized.encode('ascii', 'ignore').decode('ascii')
    # Remove characters that still break PowerShell string literals
    for ch in ("'", '"', '`', '$', '#', '\\'):
        ascii_only = ascii_only.replace(ch, ' ')
    # Collapse whitespace and cap length
    return ' '.join(ascii_only.split())[:500]


def _tts_popen(safe_text: str) -> subprocess.Popen:
    """Launch a PowerShell TTS process and return the handle."""
    return subprocess.Popen(
        ["powershell", "-NoProfile", "-Command",
         f"Add-Type -AssemblyName System.Speech; "
         f"$s = New-Object System.Speech.Synthesis.SpeechSynthesizer; "
         f"$s.Speak('{safe_text}')"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL
    )


def stop_speaking():
    """Immediately kill any ongoing TTS speech (barge-in / interrupt)."""
    global _tts_proc
    with _tts_lock:
        if _tts_proc and _tts_proc.poll() is None:
            try:
                _tts_proc.kill()
            except Exception:
                pass
            _tts_proc = None

def is_speaking() -> bool:
    """Check if the TTS engine is currently outputting audio."""
    global _tts_proc
    with _tts_lock:
        return _tts_proc is not None and _tts_proc.poll() is None


def say(text: str):
    """Speak text using Windows built-in TTS (non-blocking, interruptible)."""
    global _tts_proc
    safe = _tts_sanitize(text)

    def _run():
        global _tts_proc
        proc = _tts_popen(safe)
        with _tts_lock:
            _tts_proc = proc
        proc.wait()
        with _tts_lock:
            if _tts_proc is proc:   # don't clear if already replaced
                _tts_proc = None

    threading.Thread(target=_run, daemon=True).start()


def say_wait(text: str):
    """Speak text and BLOCK until speech is fully complete (also interruptible)."""
    global _tts_proc
    safe = _tts_sanitize(text)
    proc = _tts_popen(safe)
    with _tts_lock:
        _tts_proc = proc
    proc.wait()
    with _tts_lock:
        if _tts_proc is proc:
            _tts_proc = None


# ─────────────────────────────────────────
#  Groq Chat
# ─────────────────────────────────────────
# Thread-local flag so callers know chat() already broadcast the reply
_chat_broadcast_done = threading.local()

def chat(query: str) -> str:
    global chat_history, chat_str
    _chat_broadcast_done.value = False
    chat_history.append({"role": "user", "content": query})
    chat_str += f"Sir: {query}\n Jarvis: "
    try:
        messages = [{"role": "system", "content": SYSTEM_PROMPT}] + chat_history[-20:]
        response = _groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=messages,
            max_tokens=512
        )
        reply = response.choices[0].message.content.strip()
        chat_history.append({"role": "assistant", "content": reply})
        chat_str += f"{reply}\n"
        say(reply)
        broadcast("state", {"status": "SPEAKING", "message": "Jarvis is speaking...", "color": "green"})
        broadcast("log",   {"message": f"Jarvis: {reply}", "type": "jarvis"})
        _chat_broadcast_done.value = True
        return reply
    except Exception as e:
        log.error(f"Groq API: {str(e)}")
        return "[ERROR] Neural link failed. Check API connection."


# ─────────────────────────────────────────
#  AI File-Save Mode
# ─────────────────────────────────────────
def ai_save(prompt: str) -> str:
    try:
        response = _groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=1024
        )
        reply = response.choices[0].message.content.strip()
        os.makedirs(SAVES_DIR, exist_ok=True)
        safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in prompt[:50]).strip()
        filename  = f"{safe_name}_{random.randint(100, 9999)}.txt"
        filepath  = os.path.join(SAVES_DIR, filename)
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(f"Jarvis AI Response\nPrompt: {prompt}\n{'='*60}\n\n{reply}")
        say(f"Done, Sir. Response saved to {filename}")
        return f"[Saved] JarvisAI_Saves/{filename}\n\n{reply}"
    except Exception as e:
        log.error(f"AI Save: {str(e)}")
        return "[ERROR] Neural link failed. Check API connection."


# ─────────────────────────────────────────
#  Screen Awareness — Groq Vision
# ─────────────────────────────────────────
def screen_awareness(user_question: str = "What do you see on my screen?") -> str:
    """Take a screenshot and ask Groq Vision to describe / analyze it."""
    try:
        import pyautogui
        broadcast("state", {"status": "PROCESSING", "message": "Capturing screen...", "color": "cyan"})

        # 1. Take screenshot and encode as base64
        screenshot = pyautogui.screenshot()
        img_buffer = io.BytesIO()
        screenshot.save(img_buffer, format="PNG")
        img_b64 = base64.b64encode(img_buffer.getvalue()).decode("utf-8")

        # 2. Send to Groq Vision
        prompt_text = (
            f"You are JARVIS, Tony Stark's AI. "
            f"The user asked: '{user_question}'. "
            f"Analyze the screenshot and respond concisely as JARVIS would — "
            f"smart, helpful, and slightly witty. Address the user as Sir."
        )
        response = _groq_client.chat.completions.create(
            model=GROQ_VISION_MODEL,
            messages=[{"role": "user", "content": [
                {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{img_b64}"}},
                {"type": "text", "text": prompt_text}
            ]}],
            max_tokens=512
        )
        reply = response.choices[0].message.content.strip()
        say(reply)
        broadcast("state", {"status": "SPEAKING", "message": "Jarvis is speaking...", "color": "green"})
        broadcast("log",   {"message": f"Jarvis: {reply}", "type": "jarvis"})
        _chat_broadcast_done.value = True
        return reply

    except ImportError:
        return "⚠️ Screen awareness unavailable. Run: pip install pyautogui Pillow"
    except Exception as e:
        log.error(f"Screen awareness: {e}")
        err_str = str(e)
        if "decommissioned" in err_str or "model" in err_str.lower():
            return f"[ERROR] Vision model unavailable: {err_str[:200]}"
        return f"[ERROR] Screen analysis failed: {err_str[:150]}"


# ─────────────────────────────────────────
#  Command Processor
# ─────────────────────────────────────────

# ── Smart URL builder ──────────────────────────────────────
import re
import urllib.parse


# ── Smart Person / Entity Browser Lookup ───────────────────
# Regex patterns: each tuple is (pattern, destination)
# destination: 'wikipedia' | 'images' | 'instagram'
_ENTITY_RULES = [
    # Instagram — explicit ask
    (r"(?:show|find|open|get)\s+(?:me\s+)?(.+?)(?:'s)?\s+(?:on\s+)?instagram", "instagram"),
    (r"(.+?)\s+instagram\s*(?:profile|page|account)?\s*$",                      "instagram"),

    # Google Images — picture / photo / image
    (r"(?:show|find|get|display)\s+(?:me\s+)?(?:a\s+)?(?:picture|photo|image|pic)s?\s+(?:of\s+)?(.+?)\s*[?.]?$", "images"),
    (r"(?:picture|photo|image|pic)s?\s+of\s+(.+?)\s*[?.]?$",                    "images"),

    # Wikipedia — explicit ask
    (r"(?:search|open|find)?\s*(.+?)\s+on\s+wikipedia\s*[?.]?$",                "wikipedia"),

    # Wikipedia — general person info queries
    (r"^who\s+(?:is|was|are|were)\s+(.+?)\s*[?.]?$",                            "wikipedia"),
    (r"^(?:tell me about|what do you know about|info on|info about|information on|information about)\s+(.+?)\s*[?.]?$", "wikipedia"),
]

# Words that should NOT trigger a browser open
# Includes generic topics AND action verbs (prevents "open" in "open instagram" being treated as a name)
_SKIP_ENTITY_WORDS = {
    # generic topics
    "time", "date", "weather", "music", "news", "this", "that", "it",
    "ai", "python", "java", "code", "jarvis", "yourself", "you",
    # action verbs — stop "open instagram" matching as name="open"
    "open", "show", "find", "get", "search", "play", "watch",
    "go", "start", "launch", "browse", "visit",
    # filler
    "the", "a", "an", "my", "your",
}


def _smart_person_lookup(query: str) -> bool:
    """
    Detect if the query is about a person / entity and open a relevant browser tab.
    Returns True if a browser action was taken (does NOT block chat() from running).
    """
    q = query.strip()
    q_lower = q.lower()

    for pattern, destination in _ENTITY_RULES:
        m = re.search(pattern, q_lower, re.IGNORECASE)
        if not m:
            continue

        name = m.group(1).strip().rstrip('?.').strip()

        # Skip if too short or matches a generic skip word
        if len(name) < 2:
            continue
        name_words = set(name.lower().split())
        if name_words & _SKIP_ENTITY_WORDS:
            continue

        encoded = urllib.parse.quote_plus(name)

        if destination == "instagram":
            # Search Google for their Instagram — more reliable than guessing @username
            url = f"https://www.google.com/search?q={encoded}+instagram+official+profile"
            _open_url(url)
            broadcast("log", {"message": f"System: Searching Instagram for {name.title()}", "type": ""})
            log.info(f"Browser → Instagram search for {name!r}")
            return True

        elif destination == "images":
            url = f"https://www.google.com/search?q={encoded}&tbm=isch"
            _open_url(url)
            broadcast("log", {"message": f"System: Opening Google Images for {name.title()}", "type": ""})
            log.info(f"Browser → Google Images for {name!r}")
            return True

        elif destination == "wikipedia":
            url = f"https://en.wikipedia.org/wiki/Special:Search?search={encoded}"
            _open_url(url)
            broadcast("log", {"message": f"System: Opening Wikipedia for {name.title()}", "type": ""})
            log.info(f"Browser → Wikipedia for {name!r}")
            return True

    return False

# Sites with optional search-URL templates
SMART_SITES = {
    "youtube":   {
        "home":   "https://www.youtube.com",
        "search": "https://www.youtube.com/results?search_query={q}",
        "triggers": ["youtube"],
    },
    "google":    {
        "home":   "https://www.google.com",
        "search": "https://www.google.com/search?q={q}",
        "triggers": ["google"],
    },
    "wikipedia": {
        "home":   "https://www.wikipedia.org",
        "search": "https://en.wikipedia.org/wiki/Special:Search?search={q}",
        "triggers": ["wikipedia", "wiki"],
    },
    "github":    {
        "home":   "https://www.github.com",
        "search": "https://github.com/search?q={q}",
        "triggers": ["github"],
    },
    "reddit":    {
        "home":   "https://www.reddit.com",
        "search": "https://www.reddit.com/search/?q={q}",
        "triggers": ["reddit"],
    },
    "instagram": {"home": "https://www.instagram.com",  "search": None, "triggers": ["instagram"]},
    "twitter":   {"home": "https://www.twitter.com",    "search": None, "triggers": ["twitter", "x"]},
    "whatsapp":  {"home": "https://web.whatsapp.com",   "search": None, "triggers": ["whatsapp"]},
    "netflix":   {"home": "https://www.netflix.com",    "search": None, "triggers": ["netflix"]},
}

# Patterns for extracting search terms
_SEARCH_PATTERNS = [
    # "search [me] [a/an/for] X [on/from/in] youtube"
    r"search (?:me\s+)?(?:a\s+|an\s+|for\s+)?(.+?)(?:\s+(?:on|in|from)\s+\w+)?$",
    # "open youtube and search X"
    r"(?:open|go to) \w+ (?:and )?search(?:ing)? (?:for\s+)?(.+)$",
    # "find / look up X on/from youtube"
    r"(?:find|look up|lookup|look for) (.+?) (?:on|in|from) \w+",
    # "play / watch X on/from youtube"
    r"(?:play|watch) (.+?) (?:on|from) youtube",
    # "open X on/from youtube" / "show me X on youtube"
    r"open (.+?) (?:on|from|in) \w+",
    r"(?:show|get|give) (?:me\s+)?(.+?) (?:on|from|in) \w+",
]

def _extract_search_term(text: str) -> str | None:
    """Try to pull a search term out of a natural-language query."""
    for pattern in _SEARCH_PATTERNS:
        m = re.search(pattern, text, re.IGNORECASE)
        if m:
            term = m.group(1).strip()
            # Remove trailing filler words
            term = re.sub(r"\s+(please|now|sir|jarvis)$", "", term, flags=re.IGNORECASE)
            if term:
                return term
    return None

def _open_url(url: str):
    """Open a URL reliably."""
    try:
        webbrowser.open(url)
    except Exception:
        os.startfile(url)

def execute_system_command(query: str) -> str:
    q = query.lower().strip()
    log.info(f"CMD: {q!r}")

    # ── Special system commands (also handles text input from UI) ─────────
    if any(p in q for p in voice_engine.QUIT_WORDS):
        broadcast("state", {"status": "SHUTDOWN", "message": "Shutting down...", "color": "red"})
        broadcast("log", {"message": "Jarvis: Shutting down. Goodbye, Sir.", "type": "jarvis"})
        say("Shutting down all systems. Goodbye, Sir.")
        time.sleep(3)
        os._exit(0)

    if any(p in q for p in voice_engine.RESTART_WORDS):
        broadcast("state", {"status": "RESTART", "message": "Restarting systems...", "color": "cyan"})
        broadcast("log", {"message": "Jarvis: Restarting all systems, Sir.", "type": "jarvis"})
        say("Restarting all systems, Sir.")
        time.sleep(2)
        os.execv(sys.executable, [sys.executable] + sys.argv)

    if any(p in q for p in voice_engine.SLEEP_WORDS):
        voice_engine.sleeping = True
        broadcast("state", {"status": "SLEEP", "message": "Sleep mode active.", "color": "dim"})
        broadcast("log", {"message": "Jarvis: Entering sleep mode. Say 'Wake up Jarvis' to resume.", "type": "jarvis"})
        say("Entering sleep mode, Sir.")
        _chat_broadcast_done.value = True # prevent double log
        return "Sleep mode activated."

    if any(p in q for p in voice_engine.WAKE_UP_WORDS):
        voice_engine.sleeping = False
        broadcast("state", {"status": "WAITING", "message": "Systems restored. Listening...", "color": "cyan"})
        broadcast("log", {"message": "Jarvis: Back online, Sir.", "type": "jarvis"})
        say("I'm back online, Sir.")
        _chat_broadcast_done.value = True
        return "System restored."

    # ── Smart person / entity browser lookup (MUST run first) ─────────────
    # This intercepts "X instagram", "X on wikipedia", "who is X" etc. BEFORE
    # SMART_SITES can consume them. If a person is found, browser opens AND
    # chat() still gives the verbal answer.
    if _smart_person_lookup(query):
        return chat(query)

    # ── Smart website + search ─────────────────────────────
    for site_name, cfg in SMART_SITES.items():
        triggers = cfg["triggers"]
        matched  = any(
            (f"open {t}" in q or f"search {t}" in q or
             f"on {t}" in q or f"in {t}" in q or
             f"go to {t}" in q or f"from {t}" in q or
             q.endswith(t))   # e.g. "search python tutorial youtube"
            for t in triggers
        )
        if not matched:
            continue

        search_term = _extract_search_term(q)

        if search_term and cfg.get("search"):
            encoded = urllib.parse.quote_plus(search_term)
            url     = cfg["search"].format(q=encoded)
            _open_url(url)
            say(f"Searching {site_name} for {search_term}, Sir.")
            return f"[Search] {site_name.capitalize()}: {search_term}"
        else:
            _open_url(cfg["home"])
            say(f"Opening {site_name}, Sir.")
            return f"Opening {site_name.capitalize()}..."


    # Windows apps
    apps = {
        "notepad":       "notepad.exe",
        "calculator":    "calc.exe",
        "paint":         "mspaint.exe",
        "task manager":  "taskmgr.exe",
        "file explorer": "explorer.exe",
        "chrome":        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        "vs code":       os.path.expandvars(r"%LOCALAPPDATA%\Programs\Microsoft VS Code\Code.exe"),
        "edge":          r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    }
    for name, path in apps.items():
        if f"open {name}" in q:
            try:
                os.startfile(path)
                say(f"Accessing {name}, Sir.")
                return f"Launching {name.capitalize()}..."
            except Exception as e:
                return f"Could not launch {name}: {e}"

    if "time" in q:
        t = datetime.datetime.now().strftime("%I:%M %p")
        say(f"Sir, the time is {t}.")
        return f"Current time: {t}"

    if "date" in q:
        today = datetime.datetime.now().strftime("%A, %B %d, %Y")
        say(f"Today is {today}, Sir.")
        return f"Today is {today}"

    if "open music" in q or "play music" in q:
        music_dirs = [os.path.expanduser("~/Music"), os.path.expanduser("~/Downloads")]
        for d in music_dirs:
            if os.path.exists(d):
                for f in os.listdir(d):
                    if f.endswith((".mp3", ".wav", ".flac", ".m4a")):
                        try:
                            os.startfile(os.path.join(d, f))
                            say("Playing music, Sir.")
                            return f"Playing: {f}"
                        except Exception as e:
                            return f"Music error: {e}"
        return "No music files found in Music or Downloads folder."

    if "using artificial intelligence" in q or "use ai" in q or "ai mode" in q:
        say("Activating AI save mode, Sir.")
        return ai_save(query)

    if "reset chat" in q or "clear chat" in q or "forget everything" in q:
        global chat_history, chat_str
        chat_history = []
        chat_str     = ""
        say("Memory cleared, Sir. Starting fresh.")
        return "Chat history reset."

    if "system info" in q or "system status" in q:
        cpu = psutil.cpu_percent()
        ram = psutil.virtual_memory().percent
        say(f"CPU is at {cpu} percent and RAM at {ram} percent, Sir.")
        return f"CPU: {cpu}% | RAM: {ram}%"

    # ── Screen Awareness ──────────────────────────────────
    SCREEN_TRIGGERS = [
        "what's on my screen", "whats on my screen",
        "what is on my screen", "analyze my screen",
        "look at my screen", "read my screen",
        "what do you see", "screen analysis",
        "what's on the screen", "describe my screen",
    ]
    if any(t in q for t in SCREEN_TRIGGERS):
        say("Analyzing your screen, Sir. One moment.")
        return screen_awareness(query)

    return chat(query)


# ─────────────────────────────────────────
#  VOICE ENGINE — Always-on Wake Word
# ─────────────────────────────────────────
class VoiceEngine:
    """
    Continuously listens for the wake word in a background thread.
    Sends all state changes via SSE to connected browser clients.
    """

    WAKE_WORDS    = [
        "jarvis", "hey jarvis", "ok jarvis", "okay jarvis",
        # Partial matches — speech recognition often cuts words short
        "hey jar", "hey jarvi", "jarvi", "jar vis",
        "hey jarbis", "hey jarbus",   # common mishearings
    ]
    QUIT_WORDS    = ["jarvis quit", "shutdown jarvis", "exit jarvis", "goodbye jarvis", "jarvis shutdown"]
    RESTART_WORDS = ["jarvis restart", "restart jarvis", "reboot jarvis", "jarvis reboot"]
    SLEEP_WORDS   = ["jarvis sleep", "go to sleep jarvis", "sleep mode jarvis"]
    WAKE_UP_WORDS = ["wake up jarvis", "jarvis wake up", "jarvis resume", "come back jarvis"]

    def __init__(self):
        self.r        = sr.Recognizer()
        self.r.energy_threshold        = 200
        self.r.dynamic_energy_threshold = True
        self.running  = True
        self.sleeping = False
        self._lock    = threading.Lock()   # prevents concurrent mic access

    # ── low-level listen ──────────────────────────────────────
    def _listen(self, timeout=5, phrase_limit=5) -> str | None:
        """Blocking listen. Returns recognised text or None."""
        with self._lock:
            try:
                with sr.Microphone() as source:
                    if not is_speaking():
                        self.r.adjust_for_ambient_noise(source, duration=0.2)
                    audio = self.r.listen(source, timeout=timeout, phrase_time_limit=phrase_limit)
                return self.r.recognize_google(audio, language="en-in")
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                return None
            except Exception as e:
                log.error(f"[VOICE] Listen error: {e}")
                return None

    # ── state helpers ─────────────────────────────────────────
    def _set_state(self, status: str, message: str, color: str = "cyan"):
        log.info(f"State → {status}")
        broadcast("state", {"status": status, "message": message, "color": color})

    def _log(self, msg: str, kind: str = ""):
        broadcast("log", {"message": msg, "type": kind})
        log.info(msg)

    # ── main loop ─────────────────────────────────────────────
    def run(self):
        log.info("Wake-word engine started. Say 'Hey Jarvis' to activate.")
        self._set_state("WAITING", "Say 'Hey Jarvis' to activate...", "dim")

        while self.running:
            # ── Sleep mode ────────────────────────────────────
            if self.sleeping:
                text = self._listen(timeout=4, phrase_limit=5)
                if text and any(w in text.lower() for w in self.WAKE_UP_WORDS):
                    self.sleeping = False
                    self._set_state("WAITING", "Systems restored. Listening...", "cyan")
                    self._log("Jarvis: Back online, Sir.", "jarvis")
                    say("I'm back online, Sir.")
                continue

            # ── Phase 1: Wait for wake word ───────────────────
            # Reduce limit if speaking so barge-in is faster (less wait for silence)
            current_phrase_limit = 3 if is_speaking() else 6
            text = self._listen(timeout=5, phrase_limit=current_phrase_limit)
            if not text:
                continue

            text_lower = text.lower().strip()
            log.info(f"Heard: {text_lower!r}")

            # Check for sleep command even without full wake+command cycle
            if any(w in text_lower for w in self.SLEEP_WORDS):
                self.sleeping = True
                self._set_state("SLEEP", "Sleep mode active.", "dim")
                self._log("Jarvis: Sleep mode activated. Say 'Wake up Jarvis' to resume.", "jarvis")
                say("Entering sleep mode, Sir. Say wake up Jarvis to resume.")
                continue

            # Must contain the wake word to proceed
            if not any(w in text_lower for w in self.WAKE_WORDS):
                continue

            # ── Wake word detected! — interrupt any ongoing speech first ────
            stop_speaking()   # barge-in: kill TTS so Jarvis listens immediately
            self._set_state("WAKE", "Wake word detected!", "green")
            self._log("System: Wake word detected.", "")
            say_wait("Sir?")    # short blocking response — mic won't open until done

            # ── Phase 2: Listen for the actual command ────────
            self._set_state("LISTENING", "Listening for command...", "red")
            command = self._listen(timeout=10, phrase_limit=15)

            if not command:
                self._set_state("WAITING", "No command detected. Waiting...", "dim")
                say("I didn't catch that, Sir. Please try again.")
                continue

            command_lower = command.lower().strip()
            self._log(f"User: {command}", "user")

            # ── Special system commands ───────────────────────
            if any(p in command_lower for p in self.QUIT_WORDS):
                self._set_state("SHUTDOWN", "Shutting down...", "red")
                self._log("Jarvis: Shutting down. Goodbye, Sir.", "jarvis")
                say("Shutting down all systems. Goodbye, Sir.")
                time.sleep(3)
                os._exit(0)

            if any(p in command_lower for p in self.RESTART_WORDS):
                self._set_state("RESTART", "Restarting systems...", "cyan")
                self._log("Jarvis: Restarting all systems, Sir.", "jarvis")
                say("Restarting all systems, Sir.")
                time.sleep(2)
                os.execv(sys.executable, [sys.executable] + sys.argv)

            if any(p in command_lower for p in self.SLEEP_WORDS):
                self.sleeping = True
                self._set_state("SLEEP", "Sleep mode active.", "dim")
                self._log("Jarvis: Entering sleep mode. Say 'Wake up Jarvis' to resume.", "jarvis")
                say("Entering sleep mode, Sir.")
                continue

            # ── Normal command → process ──────────────────
            self._set_state("PROCESSING", "Processing command...", "cyan")
            _chat_broadcast_done.value = False   # reset before every command (thread reuse fix)
            response = execute_system_command(command)
            # chat() already broadcasts AI replies — only log system command results
            if not getattr(_chat_broadcast_done, 'value', False):
                self._log(f"Jarvis: {response}", "jarvis")
            self._set_state("WAITING", "Say 'Hey Jarvis' to activate...", "dim")


# Global engine instance (started at boot)
voice_engine = VoiceEngine()


# ─────────────────────────────────────────
#  Flask Routes
# ─────────────────────────────────────────
@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/<path:path>')
def static_files(path):
    return send_from_directory('frontend', path)

@app.route('/api/stats')
def get_stats():
    return jsonify({
        "cpu": psutil.cpu_percent(interval=0.2),
        "ram": psutil.virtual_memory().percent
    })

@app.route('/api/command', methods=['POST'])
def command_api():
    """Manual text command from the UI input box."""
    data  = request.json or {}
    query = data.get('query', '').strip()
    if not query:
        return jsonify({"response": "No command received."})
    # Reset broadcast flag at the START of every request (thread pool reuse fix)
    _chat_broadcast_done.value = False
    broadcast("log",   {"message": f"User: {query}", "type": "user"})
    broadcast("state", {"status": "PROCESSING", "message": "Processing...", "color": "cyan"})
    response = execute_system_command(query)
    # chat() already broadcasts AI replies — only broadcast system command results
    if not getattr(_chat_broadcast_done, 'value', False):
        broadcast("log", {"message": f"Jarvis: {response}", "type": "jarvis"})
    
    if voice_engine.sleeping:
        # If we entered sleep mode, make sure we broadcast SLEEP, not WAITING
        broadcast("state", {"status": "SLEEP", "message": "Sleep mode active.", "color": "dim"})
    else:
        broadcast("state", {"status": "WAITING", "message": "Say 'Hey Jarvis' to activate...", "color": "dim"})
    return jsonify({"response": response})

@app.route('/api/voice', methods=['GET'])
def voice_api():
    """
    Manual mic trigger (fallback when wake word isn't detected).
    Pauses the engine, takes one recording, resumes engine.
    """
    if voice_engine._lock.locked():
        return jsonify({"query": "", "error": "Mic in use by voice engine"})
    broadcast("state", {"status": "LISTENING", "message": "Manual listen mode...", "color": "red"})
    r = sr.Recognizer()
    try:
        with voice_engine._lock:
            with sr.Microphone() as source:
                r.adjust_for_ambient_noise(source, duration=0.4)
                audio = r.listen(source, timeout=6, phrase_time_limit=12)
                query = r.recognize_google(audio, language="en-in")
                return jsonify({"query": query})
    except Exception:
        return jsonify({"query": ""})
    finally:
        broadcast("state", {"status": "WAITING", "message": "Say 'Hey Jarvis' to activate...", "color": "dim"})

@app.route('/api/stream')
def sse_stream():
    """Server-Sent Events endpoint — frontend subscribes here for live state."""
    def generate():
        q = queue.Queue(maxsize=50)
        sse_subscribers.append(q)
        # Send immediate hello + current state so browser syncs instantly
        yield f"data: {json.dumps({'type':'connected','data':{}})}\n\n"
        # Replay last known state so a reconnecting browser doesn't miss it
        yield f"data: {json.dumps({'type':'state','data':_current_state})}\n\n"
        try:
            while True:
                try:
                    payload = q.get(timeout=25)
                    yield f"data: {payload}\n\n"
                except queue.Empty:
                    yield ": heartbeat\n\n"   # keep connection alive
        except GeneratorExit:
            pass
        finally:
            if q in sse_subscribers:
                sse_subscribers.remove(q)

    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'X-Accel-Buffering': 'no'
        }
    )

@app.route('/api/engine/sleep', methods=['POST'])
def engine_sleep():
    voice_engine.sleeping = True
    broadcast("state", {"status": "SLEEP", "message": "Sleep mode active.", "color": "dim"})
    return jsonify({"status": "sleeping"})

@app.route('/api/engine/wake', methods=['POST'])
def engine_wake():
    voice_engine.sleeping = False
    broadcast("state", {"status": "WAITING", "message": "Say 'Hey Jarvis' to activate...", "color": "dim"})
    return jsonify({"status": "awake"})

@app.route('/api/saves')
def list_saves():
    if not os.path.exists(SAVES_DIR):
        return jsonify({"files": []})
    files = sorted(
        [f for f in os.listdir(SAVES_DIR) if f.endswith(".txt")],
        key=lambda f: os.path.getmtime(os.path.join(SAVES_DIR, f)),
        reverse=True
    )
    return jsonify({"files": files})


# ─────────────────────────────────────────
#  Entry Point
# ─────────────────────────────────────────
def run_server():
    app.run(port=5000, debug=False, use_reloader=False, threaded=True)

if __name__ == "__main__":
    print("=" * 55)
    print("  JARVIS AI -- Neural Interface Initializing...")
    print("  Dashboard -> http://localhost:5000")
    print("  Wake word -> 'Hey Jarvis' or 'Jarvis'")
    print("  Shutdown  -> 'Jarvis quit'")
    print("  Restart   -> 'Jarvis restart'")
    print("  Sleep     -> 'Jarvis sleep'")
    print("=" * 55)

    # Start Flask server
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()

    # Start always-on voice engine
    engine_thread = threading.Thread(target=voice_engine.run, daemon=True)
    engine_thread.start()

    time.sleep(2)
    webbrowser.open("http://localhost:5000")
    say("System online. Welcome back, Sir. Say Hey Jarvis to begin.")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n[JARVIS] Shutting down.")
