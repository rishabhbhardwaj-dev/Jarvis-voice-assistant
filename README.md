# ⚡ JARVIS AI — Always-On Neural Interface

> *"Sometimes you gotta run before you can walk."* — Tony Stark

A fully voice-activated AI desktop assistant powered by **Groq AI (Llama 3.3)**, featuring a live 3D neural orb dashboard, real-time state-driven UI, screen awareness, smart person lookup, and natural-language command parsing.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=flat&logo=flask&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-Llama%203.3-F55036?style=flat)
![Three.js](https://img.shields.io/badge/Three.js-3D%20Orb-black?style=flat&logo=three.js)
![Windows](https://img.shields.io/badge/Platform-Windows-0078D6?style=flat&logo=windows)

---

## 🔥 Features

| Feature | Description |
|---|---|
| 🎙️ **Always-On Wake Word** | Say *"Hey Jarvis"* anytime — no button needed |
| 🧠 **Groq AI Brain** | Powered by Llama 3.3-70B (chat) + Llama 4 Scout (vision) |
| 🌐 **Real-Time Dashboard** | 3D Three.js neural orb synced to voice states |
| 💬 **Chat Bubble UI** | Conversation panel — user right / Jarvis left |
| 📡 **SSE Live Sync** | Voice + text appear in UI simultaneously |
| 🔍 **Smart Commands** | *"Search YouTube for python tutorial"* → opens search URL |
| 👁️ **Screen Awareness** | *"What's on my screen?"* → Groq Vision analyzes it live |
| 🔇 **Barge-In / Interrupt** | Say *"Hey Jarvis"* mid-speech to instantly silence him |
| 🕵️ **Person Lookup** | *"Who is Rohit Sharma?"* → opens Wikipedia + answers |
| 📸 **Smart Image Search** | *"Show picture of Virat Kohli"* → Google Images |
| 📱 **Instagram Finder** | *"Rohit Sharma Instagram"* → finds their profile |
| 😴 **Sleep / Wake Mode** | *"Jarvis sleep"* / *"Wake up Jarvis"* |
| 💾 **AI File Save** | *"Use AI to write..."* → saves response to file |
| 📊 **System Monitoring** | Live CPU & RAM stats on dashboard |
| 🔄 **Hot Restart** | *"Jarvis restart"* — no manual restart needed |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│                   JARVIS SYSTEM                      │
│                                                     │
│  ┌──────────────┐      ┌──────────────────────────┐ │
│  │  VoiceEngine │─────▶│   execute_system_command │ │
│  │  (Thread)    │      │   - Smart site search    │ │
│  │  Wake word   │      │   - App launcher         │ │
│  │  detection   │      │   - Screen awareness     │ │
│  └──────┬───────┘      │   - Claude AI chat       │ │
│         │              └────────────┬─────────────┘ │
│         │ SSE broadcast             │ say() + SSE   │
│         ▼                          ▼               │
│  ┌──────────────────────────────────────────────┐  │
│  │         Flask Server  (port 5000)            │  │
│  │  /api/stream  /api/command  /api/voice       │  │
│  └──────────────────────┬───────────────────────┘  │
│                         │ HTTP + SSE                │
│                         ▼                           │
│  ┌──────────────────────────────────────────────┐  │
│  │         Browser Dashboard (frontend/)        │  │
│  │  Three.js Orb │ Chat UI │ Status │ Stats     │  │
│  └──────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### 1 — Prerequisites
- Python 3.11+
- Windows OS (uses PowerShell TTS)
- A microphone

### 2 — Install dependencies
```bash
pip install -r requirements.txt
```
> If pyaudio fails: `pip install pipwin` then `pipwin install pyaudio`

### 3 — Add your API Key
Open `config.py` and paste your Groq key:
```python
groq_api_key = "gsk_your-key-here"
```
Get a free key at: https://console.groq.com

### 4 — Launch Jarvis
```bash
python main.py
```
Or double-click `run_jarvis.bat`

Dashboard opens automatically at → **http://localhost:5000**

---

## 🎙️ Voice Command Reference

### Wake & Control
| Say | Action |
|---|---|
| `"Hey Jarvis"` | Wake up |
| `"Jarvis sleep"` | Enter sleep mode |
| `"Wake up Jarvis"` | Resume from sleep |
| `"Jarvis restart"` | Hot restart |
| `"Jarvis quit"` | Shut down |

### Smart Web Commands
| Say | Action |
|---|---|
| `"Open YouTube"` | Opens YouTube |
| `"Search YouTube for lofi music"` | Searches YouTube |
| `"Search Google for AI news"` | Google search |
| `"Find react hooks on GitHub"` | GitHub search |
| `"Look up quantum physics on Wikipedia"` | Wikipedia search |

### Person & Entity Lookup
| Say | Action |
|---|---|
| `"Who is Rohit Sharma?"` | Opens Wikipedia + verbal answer |
| `"Tell me about Elon Musk"` | Opens Wikipedia + verbal answer |
| `"Show me picture of Virat Kohli"` | Opens Google Images |
| `"Photo of Cristiano Ronaldo"` | Opens Google Images |
| `"Rohit Sharma Instagram"` | Finds their Instagram profile |
| `"Show Sachin on Instagram"` | Finds their Instagram profile |

### System
| Say | Action |
|---|---|
| `"What time is it"` | Current time |
| `"What's the date"` | Today's date |
| `"System status"` | CPU & RAM usage |
| `"Open Notepad / Calculator / VS Code"` | Launch apps |
| `"Play music"` | Play local music files |

### AI Features
| Say | Action |
|---|---|
| `"What's on my screen?"` | Screen analysis via Groq Vision |
| `"Analyze my screen"` | Screen analysis via Groq Vision |
| `"Use AI to write a cover letter"` | AI response saved to file |
| `"Reset chat"` | Clear conversation memory |
| Anything else | Chat with Groq AI (Llama 3.3) |

---

## 📁 Project Structure

```
jarvis_files_by_claude/
├── main.py              # Core backend — Flask + Voice + AI
├── config.py            # API key (do NOT commit this)
├── requirements.txt     # Python dependencies
├── run_jarvis.bat       # One-click launcher
├── .gitignore
└── frontend/
    ├── index.html       # Dashboard layout
    ├── style.css        # Premium dark UI + state animations
    └── script.js        # Three.js orb + SSE client + chat UI
```

---

## 🛠️ Troubleshooting

| Problem | Fix |
|---|---|
| Mic not working | Set as default in Windows Sound Settings |
| PyAudio error | `pip install pipwin` → `pipwin install pyaudio` |
| API key error | Check `config.py` — key must start with `gsk_` |
| Screen awareness fails | `pip install pyautogui Pillow` |
| Port 5000 in use | Kill other processes using port 5000 |
| Jarvis won't stop talking | Say "Hey Jarvis" to interrupt mid-speech |

---

## 🧑‍💻 Demo Steps (for presentations)

1. Start: `python main.py` — dashboard opens in browser
2. Say **"Hey Jarvis"** — orb turns green, UI flashes
3. Say **"What time is it"** — Jarvis speaks + chat bubble appears
4. Say **"Search YouTube for Iron Man theme"** — browser opens search
5. Say **"Who is Elon Musk?"** — Wikipedia opens + Jarvis answers
6. Say **"What's on my screen?"** — Groq Vision analyzes the screen live
7. Let Jarvis talk, then say **"Hey Jarvis"** again — he stops instantly! (barge-in)
8. Say **"Jarvis sleep"** — entire UI dims
9. Say **"Wake up Jarvis"** — UI restores
10. Type a question in the input box — chat bubble response
11. Say **"Jarvis quit"** — clean shutdown

---

*Built with ❤️ using Groq AI (Llama) + Flask + Three.js*
