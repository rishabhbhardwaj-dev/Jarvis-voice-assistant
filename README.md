# JARVIS AI — Desktop Voice Assistant & Neural Interface

A voice-activated, multimodal desktop assistant built with Python, Flask, and the Groq Cloud API, featuring an always-on speech recognition loop, interruptible Windows Text-to-Speech (TTS), deterministic command routing, and a real-time 3D Three.js neural dashboard synchronized via Server-Sent Events (SSE).

![Platform](https://img.shields.io/badge/Platform-Windows-0078D6?style=flat&logo=windows)
![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.x%20%2F%203.x-000000?style=flat&logo=flask&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-Cloud%20API-F55036?style=flat)
![Three.js](https://img.shields.io/badge/Three.js-r128%20WebGL-black?style=flat&logo=three.js)

---

## 1. Overview

**JARVIS AI** is an event-driven desktop assistant for Windows designed to combine conversational AI, desktop automation, and a visual HUD interface into a cohesive workflow.

The system continuously monitors microphone input for a configurable wake word, acknowledges queries using out-of-process speech synthesis, routes commands through a deterministic pattern-matching engine, and delegates natural-language queries and screen analysis to Groq-hosted language and vision models.

All assistant state transitions, logs, and conversational turns are broadcast in real time to a local browser dashboard via Server-Sent Events (SSE), dynamically controlling a Three.js 3D WebGL Neural Orb visualizer.

---

## 2. Verified Features

| Feature | Description | Implementation Status |
|---|---|---|
| **Always-On Wake Word** | Continuous background microphone listener detecting phrases such as *"Hey Jarvis"*, *"Jarvis"*, and common phonetic variants. | Verified in `main.py` |
| **Barge-In / Instant Interruption** | Immediately terminates active speech synthesis upon detecting the wake word during assistant speech output. | Verified in `main.py` |
| **Interruptible Windows TTS** | Spawns out-of-process PowerShell scripts leveraging the .NET `System.Speech.Synthesis.SpeechSynthesizer` assembly. | Verified in `main.py` |
| **Conversational LLM** | Handles natural-language dialogues with a sliding-window context of the last 20 messages via Groq API. | Verified in `main.py` |
| **In-Memory Screen Awareness** | Captures display frames via PyAutoGUI directly into an in-memory byte buffer and queries Groq Vision (`GROQ_VISION_MODEL`). | Verified in `main.py` |
| **Deterministic Command Dispatch** | Pattern-matching engine for opening websites, launching desktop applications, searching media, and querying local time/date. | Verified in `main.py` |
| **Entity & Person Lookup** | Regex parser detecting inquiries about people, opening targeted searches across Google Images, Wikipedia, or Instagram while simultaneously returning an LLM answer. | Verified in `main.py` |
| **Real-Time 3D HUD Dashboard** | Interactive Three.js WebGL visualizer dynamically altering geometry rotation, breathing amplitude, and colors based on assistant status. | Verified in `frontend/` |
| **Live SSE State Synchronization** | Half-duplex HTTP event streaming (`text/event-stream`) pushing state changes (`WAITING`, `WAKE`, `LISTENING`, `PROCESSING`, `SPEAKING`, `SLEEP`) to browser clients. | Verified in `main.py` |
| **System Resource Telemetry** | Displays real-time CPU and RAM utilization polled via `psutil`. | Verified in `main.py` |
| **AI File Save Mode** | Writes generated AI responses to structured, timestamped text files inside `JarvisAI_Saves/`. | Verified in `main.py` |
| **Sleep / Wake Modes & Hot Restart** | Low-power sleep state ignoring general speech until awakened, and process replacement via `os.execv` for instant reloads. | Verified in `main.py` |

> [!NOTE]
> **Dashboard Reality Check**: The central Three.js Neural Orb, status glow, terminal logs, and chat feed are live representations of backend state. However, peripheral sidebar widgets (Network Stability %, Upcoming Tasks, Active Module toggles, and the Sentiment Analysis gauge) are simulated front-end HTML/CSS/JS elements and are not connected to live background services.

---

## 3. How It Works

JARVIS operates as a concurrent multi-threaded system divided into audio capture, command routing, external AI processing, and browser event streaming:

```text
                             USER INPUT
                     (Microphone Audio / Web Chat)
                                  │
                                  ▼
               ┌─────────────────────────────────────┐
               │         VoiceEngine Loop            │
               │  - sr.Microphone() capture          │
               │  - Google Speech Recognition API    │
               │  - Wake-word regex matching         │
               └──────────────────┬──────────────────┘
                                  │
                          Wake Word Detected
                                  │
                                  ▼
               ┌─────────────────────────────────────┐
               │    Barge-In / Acoustic Control      │
               │  - stop_speaking(): kill TTS proc   │
               │  - say_wait("Sir?"): block mic      │
               │  - Listen for user command (10s)    │
               └──────────────────┬──────────────────┘
                                  │
                                  ▼
               ┌─────────────────────────────────────┐
               │      execute_system_command()       │
               │  - Regex / keyword inspection       │
               └──────────┬───────────────────┬──────┘
                          │                   │
                Deterministic Match       No Match
                          │                   │
                          ▼                   ▼
               ┌────────────────────┐ ┌────────────────────┐
               │   System Action    │ │     Groq Cloud     │
               │ - os.startfile()   │ │ - Chat Completion  │
               │ - webbrowser.open()│ │ - Vision (Base64)  │
               │ - Process Control  │ │ - 20-Turn History  │
               └──────────┬─────────┘ └─────────┬──────────┘
                          │                     │
                          └──────────┬──────────┘
                                     │
                                     ▼
               ┌─────────────────────────────────────┐
               │        Response Dispatcher          │
               │  - PowerShell System.Speech TTS     │
               │  - broadcast() SSE State & Logs     │
               └──────────────────┬──────────────────┘
                                  │
                                  ▼
               ┌─────────────────────────────────────┐
               │      Three.js Browser Dashboard     │
               │  - EventSource('/api/stream')       │
               │  - Dynamic 3D Orb rotation & color  │
               │  - Live conversation bubbles        │
               └─────────────────────────────────────┘
```

### Detailed Pipeline Breakdown
1. **Audio Capture**: `VoiceEngine._listen()` opens the microphone using `speech_recognition`. To avoid calibrating on speaker output, ambient noise adjustment is skipped while speech is active. Audio chunks are sent to Google's Speech Recognition endpoint (`language="en-in"`).
2. **Acoustic Coordination & Feedback Prevention**:
   - When a wake word is recognized, `stop_speaking()` immediately terminates any active TTS process (`_tts_proc.kill()`).
   - The assistant then executes `say_wait("Sir?")`, a blocking call that holds the voice thread until the spoken greeting ends. This guarantees the microphone will not capture the assistant's own voice.
3. **Command Processing**:
   - Matches are evaluated through `execute_system_command()`.
   - Deterministic commands (app launches, web navigation, person lookup, system stats) run directly via Python standard libraries.
   - General conversational queries fall through to `chat()`, which appends the prompt to the sliding history and calls the Groq Cloud API.
4. **State Streaming**:
   - State updates (`WAITING`, `WAKE`, `LISTENING`, `PROCESSING`, `SPEAKING`, `SLEEP`) and log messages are placed into client FIFO queues via `broadcast()`.
   - Connected browser sessions receive these events over HTTP chunked streaming (`/api/stream`).
5. **3D Visualization**:
   - `frontend/script.js` parses incoming SSE payloads.
   - The Three.js animation loop updates the rotation speed, scale breathing factor, and material colors of the 3D Neural Orb to reflect the current operational state.

---

## 4. Technology Stack

### Backend & Core Systems
- **Python 3.11+**: Primary application runtime.
- **Flask & Flask-CORS**: HTTP server hosting REST endpoints, serving static UI assets, and driving the SSE stream.
- **SpeechRecognition & PyAudio**: Captures microphone audio and interfaces with the Google Web Speech API.
- **Windows PowerShell (`System.Speech`)**: Out-of-process text-to-speech engine using the .NET `SpeechSynthesizer` assembly. *(Note: `pyttsx3` is not used in this codebase)*.
- **Groq Python SDK**: Cloud inference client for fast language and vision completions.
- **PyAutoGUI & Pillow**: In-memory display capture and image processing for screen analysis.
- **psutil**: Operating-system resource monitoring for CPU and memory usage statistics.
- **python-dotenv**: Environment configuration loader.

### Frontend HUD & Visualization
- **HTML5 & Vanilla CSS3**: Cyberpunk glassmorphism layout, scanline overlays, and responsive typography (Orbitron, Rajdhani).
- **JavaScript (ES6+)**: EventSource client for SSE, REST client for manual inputs, and UI state manager.
- **Three.js (r128)**: WebGL-based 3D scene rendering nested Icosahedron wireframes, orbital Torus rings, and an interactive particle field.

### Dependency Note
- `google-genai` is declared in `requirements.txt` from exploratory development, but is **not imported or used** anywhere in the active codebase.

---

## 5. Project Structure

```text
JARVIS AI/
├── config.py                       # Loads environment variables via python-dotenv
├── main.py                         # Core application: Flask server, VoiceEngine, TTS, and command router
├── requirements.txt                # Python package dependencies
├── run_jarvis.bat                  # Windows batch launcher script
├── .env.example                    # Template for Groq API keys and model configuration
├── .gitignore                      # Git exclusion rules
├── JARVIS_REFINEMENT_PROGRESS.md   # Architectural roadmap and Phase 1 modernization log
├── README.md                       # Repository documentation
├── tools/                          # Modernization layer (Phase 1: Tool Registry foundation)
│   ├── __init__.py                 # Exports BaseTool, ToolRegistry, and global registry singleton
│   ├── base.py                     # BaseTool ABC with OpenAI/Groq JSON Schema generator
│   └── registry.py                 # ToolRegistry container for registration, lookup, and safe execution
├── frontend/                       # Web dashboard assets served directly by Flask
│   ├── index.html                  # HUD interface structure and canvas container
│   ├── script.js                   # Three.js 3D orb engine, SSE subscriber, and UI controller
│   └── style.css                   # Cyberpunk theme, animations, and layout styling
├── demo/                           # Video demonstrations
│   ├── Jarvis_SleepMode.mp4        # Video demo of voice sleep mode activation
│   └── Opening_YouTube.mp4         # Video demo of automated YouTube navigation
├── screenshots/                    # Documentation screenshots
│   ├── Jarvis_Interface(Dashboard).png
│   └── Voice Command Execution.png
└── JarvisAI_Saves/                 # Output folder for files generated by ai_save()
    └── *.txt
```

> [!IMPORTANT]
> **Tool Registry Status**: The `tools/` package was established in October 2026 as Phase 1 of an architectural modernization to support OpenAI/Groq function calling. It is currently maintained as an isolated foundation and is **not yet imported or invoked** by `main.py`.

---

## 6. Prerequisites

- **Operating System**: Windows 10 or Windows 11 (required for PowerShell `System.Speech` TTS and `os.startfile` desktop automation).
- **Python**: Version 3.11 or higher.
- **Hardware**: Functional microphone and audio output (speakers or headphones).
- **Network**: Active internet connection (required for Google Speech Recognition and Groq Cloud API).
- **Groq API Key**: A valid key obtained from [console.groq.com](https://console.groq.com).

---

## 7. Setup and Installation

### 1. Clone the Repository
```bash
git clone https://github.com/rishabhbhardwaj-dev/Jarvis-voice-assistant.git
cd Jarvis-voice-assistant
```

### 2. Create and Activate a Virtual Environment
```bash
python -m venv venv
venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

> [!TIP]
> **PyAudio on Windows**: If installing `pyaudio` fails during wheel building, install precompiled wheels via `pipwin`:
> ```bash
> pip install pipwin
> pipwin install pyaudio
> ```

---

## 8. Configuration

Copy the sample environment file to create your local `.env`:

```bash
copy .env.example .env
```

Open `.env` in any text editor and configure your credentials:

```env
GROQ_API_KEY=your_actual_groq_api_key_here
GROQ_MODEL=openai/gpt-oss-120b
GROQ_VISION_MODEL=qwen/qwen3.8-27b
```

### Configuration Parameters
- `GROQ_API_KEY` *(Required)*: Your Groq API authentication token.
- `GROQ_MODEL` *(Optional, default: `openai/gpt-oss-120b`)*: The Groq chat model ID used for conversational interactions.
- `GROQ_VISION_MODEL` *(Optional, default: `qwen/qwen3.8-27b`)*: The Groq multimodal model ID used for desktop screen analysis.

---

## 9. Running JARVIS

Start the application using the Windows batch launcher:
```bash
run_jarvis.bat
```

Or run the Python entry point directly from your terminal:
```bash
python main.py
```

### Startup Sequence
1. Flask initializes and binds to `http://localhost:5000`.
2. The `VoiceEngine` background thread starts listening for the wake word.
3. The default web browser automatically launches to `http://localhost:5000`.
4. JARVIS announces: *"System online. Welcome back, Sir. Say Hey Jarvis to begin."*

---

## 10. Voice Commands and Interaction

### Wake & Lifecycle Commands
| Trigger Phrase | Behavior |
|---|---|
| `"Hey Jarvis"`, `"Jarvis"`, `"Ok Jarvis"` | Wakes the assistant, interrupts any ongoing speech, and responds *"Sir?"*. |
| `"Jarvis sleep"`, `"Go to sleep Jarvis"` | Pauses command processing; assistant enters low-power sleep state. |
| `"Wake up Jarvis"`, `"Jarvis resume"` | Restores the assistant to active listening state. |
| `"Jarvis restart"`, `"Restart Jarvis"` | Performs a hot restart of the application process via `os.execv`. |
| `"Jarvis quit"`, `"Shutdown Jarvis"`, `"Exit Jarvis"` | Speaks a closing remark and terminates the process via `os._exit(0)`. |

### Web Search & Navigation
| Trigger Phrase | Behavior |
|---|---|
| `"Open YouTube"`, `"Go to YouTube"` | Opens YouTube homepage in the default browser. |
| `"Search YouTube for [query]"`, `"Play [query] on YouTube"` | Opens YouTube search results for the extracted query. |
| `"Search Google for [query]"` | Opens Google search results for the extracted query. |
| `"Find [query] on GitHub"` | Opens GitHub repository search results. |
| `"Look up [query] on Wikipedia"` | Opens Wikipedia search results. |
| `"Open [Reddit / Instagram / Twitter / WhatsApp / Netflix]"` | Opens the corresponding web application. |

### Entity & Person Lookup
| Trigger Phrase | Behavior |
|---|---|
| `"Who is [Person]?"`, `"Tell me about [Person]"` | Opens Wikipedia search for the person and provides a spoken LLM response. |
| `"Show me a picture of [Person]"`, `"Photo of [Person]"` | Opens Google Images search results for the person. |
| `"[Person] Instagram"` | Opens a targeted Google search for the person's official Instagram profile. |

### Desktop Applications & System Telemetry
| Trigger Phrase | Behavior |
|---|---|
| `"Open Notepad"` | Launches Windows Notepad (`notepad.exe`). |
| `"Open Calculator"` | Launches Windows Calculator (`calc.exe`). |
| `"Open Paint"` | Launches Microsoft Paint (`mspaint.exe`). |
| `"Open Task Manager"` | Launches Windows Task Manager (`taskmgr.exe`). |
| `"Open File Explorer"` | Launches Windows Explorer (`explorer.exe`). |
| `"Open Chrome"` | Launches Google Chrome from standard program files. |
| `"Open VS Code"` | Launches Visual Studio Code from local AppData. |
| `"System status"`, `"System info"` | Speaks and logs current CPU and RAM utilization. |
| `"What time is it"`, `"What's the date"` | Speaks and returns local system time and date. |
| `"Play music"`, `"Open music"` | Scans `~/Music` and `~/Downloads` for audio files and plays the first match. |

### AI & Vision Commands
| Trigger Phrase | Behavior |
|---|---|
| `"What's on my screen?"`, `"Analyze my screen"` | Captures an in-memory desktop screenshot and queries Groq Vision for an analysis. |
| `"Use AI to [prompt]"`, `"AI mode [prompt]"` | Activates `ai_save()`, prompting the LLM and saving the full output to `JarvisAI_Saves/`. |
| `"Reset chat"`, `"Clear chat"`, `"Forget everything"` | Clears the multi-turn conversational history array. |
| *[Any arbitrary question]* | Sent directly to the Groq LLM for a concise, 1–2 sentence answer. |

---

## 11. API Endpoints and Real-Time Updates

Flask hosts both REST endpoints and the real-time SSE stream:

| Endpoint | Method | Purpose | Payload / Response |
|---|---|---|---|
| `/` | `GET` | Serves the main HUD dashboard. | HTML (`frontend/index.html`) |
| `/api/stream` | `GET` | SSE stream emitting real-time assistant events. | `text/event-stream` (`state`, `log`, `connected`) |
| `/api/command` | `POST` | Executes a text command sent from the web chat input. | Request: `{"query": "string"}`<br>Response: `{"response": "string"}` |
| `/api/voice` | `GET` | Manual microphone trigger (fallback when wake word is not heard). | Response: `{"query": "string"}` |
| `/api/stats` | `GET` | Telemetry endpoint returning system metrics. | Response: `{"cpu": float, "ram": float}` |
| `/api/engine/sleep` | `POST` | Transitions the voice engine into sleep state via HTTP. | Response: `{"status": "sleeping"}` |
| `/api/engine/wake` | `POST` | Restores the voice engine from sleep state via HTTP. | Response: `{"status": "awake"}` |
| `/api/saves` | `GET` | Returns a list of generated AI save files. | Response: `{"files": ["filename.txt", ...]}` |

### Server-Sent Events Protocol
Clients subscribe via JavaScript `EventSource('/api/stream')`. The stream dispatches JSON messages in the following structure:

```json
{
  "type": "state",
  "data": {
    "status": "PROCESSING",
    "message": "Processing command...",
    "color": "cyan"
  }
}
```

- **`type: "connected"`**: Emitted on connection, followed immediately by a replay of the latest known state.
- **`type: "state"`**: Updates dashboard state indicators (`WAITING`, `WAKE`, `LISTENING`, `PROCESSING`, `SPEAKING`, `SLEEP`, `SHUTDOWN`, `RESTART`).
- **`type: "log"`**: Streams real-time transcript lines categorized by sender (`"user"`, `"jarvis"`, or system messages).
- **Heartbeat (`: heartbeat\n\n`)**: Sent every 25 seconds during idle periods to keep the HTTP socket open.

---

## 12. Limitations and Platform Compatibility

- **Windows Platform Dependency**: The speech synthesis pipeline relies directly on Windows PowerShell calling the .NET `System.Speech.Synthesis` namespace, and desktop application launching uses `os.startfile`. These features do not operate on macOS or Linux without modification.
- **Fixed Executable Paths**: Desktop shortcuts for applications such as Google Chrome and VS Code use standard Windows installation paths (`C:\Program Files\Google\Chrome\...` and `%LOCALAPPDATA%\Programs\...`). If installed in non-standard directories, launch commands will report an error.
- **Cloud Speech Latency & Rate Limits**: Speech recognition requires active internet access to stream audio chunks to Google's public speech recognition endpoint. This public endpoint has no service-level agreement and may throttle requests during heavy use.
- **In-Memory Conversation History**: Multi-turn dialogue history is maintained in an in-memory Python array capped at 20 turns. Conversation memory does not persist across application restarts.
- **Simulated HUD Elements**: Certain dashboard widgets (Network Stability percentage, Upcoming Tasks, Sentiment Gauge, and Active Module toggles) are static front-end mockups designed for aesthetic purposes, rather than live integrations with backend services.

---

## 13. Troubleshooting

| Issue | Root Cause | Solution |
|---|---|---|
| **Microphone not detected** | Default recording device misconfigured or missing permissions. | Set the primary microphone as the default recording device in Windows Sound Settings and verify Python has microphone permissions. |
| **PyAudio installation errors** | Missing C++ build tools on Windows. | Run `pip install pipwin` followed by `pipwin install pyaudio`. |
| **`[ERROR] Neural link failed`** | Missing or invalid Groq API key in `.env`. | Verify that `.env` contains a valid `GROQ_API_KEY` from [console.groq.com](https://console.groq.com) and restart the application. |
| **Port 5000 already in use** | Another instance of JARVIS or local web server is running. | Terminate the process using port 5000 via Task Manager or run `netstat -ano \| findstr :5000` to find and kill the conflicting PID. |
| **Screen awareness fails** | PyAutoGUI or Pillow is not installed. | Ensure all requirements are installed: `pip install pyautogui Pillow`. |
| **Assistant talks over user** | Wake word not detected during speech. | Ensure you speak the wake word clearly (*"Hey Jarvis"*). The barge-in mechanism will immediately kill the active speech process. |

---

## 14. Modernization Roadmap

The project is undergoing an incremental refactoring documented in [`JARVIS_REFINEMENT_PROGRESS.md`](JARVIS_REFINEMENT_PROGRESS.md) to evolve into a fully agentic multimodal assistant:

- [x] **Phase 0: Architectural Inspection** — Codebase audit and separation of concerns analysis.
- [x] **Phase 1: Tool Registry Foundation** — Implemented `BaseTool` abstraction and `ToolRegistry` in `tools/` with OpenAI/Groq schema generation.
- [ ] **Phase 2: Incremental Tool Migration** *(Planned)* — Refactor deterministic system actions (app launcher, browser searches, telemetry) into isolated `BaseTool` subclasses.
- [ ] **Phase 3: LLM Function Calling Layer** *(Planned)* — Connect `ToolRegistry` to Groq function calling, replacing regex string matching with model-driven tool dispatch.
- [ ] **Phase 4: Agent Runtime** *(Planned)* — Implement a multi-step Planner / Executor / Verifier execution loop.
- [ ] **Phase 5: Persistent Memory** *(Planned)* — Introduce SQLite/vector storage for conversation recall across application restarts.
- [ ] **Phase 6: Security & Permission Policy** *(Planned)* — Add confirmation boundaries for destructive OS operations.

---

## 15. Screenshots and Demos

### JARVIS Dashboard
![JARVIS Dashboard](./screenshots/Jarvis_Interface(Dashboard).png)

### Voice Command Execution
![Voice Command Execution](./screenshots/Voice%20Command%20Execution.png)

### Video Demonstrations
- [Sleep Mode Voice Activation](./demo/Jarvis_SleepMode.mp4)
- [Automated YouTube Navigation](./demo/Opening_YouTube.mp4)

---

## 16. Author & Contact

**Rishabh Bhardwaj**

- **Portfolio**: [https://rishabh-portfolio-lac.vercel.app/](https://rishabh-portfolio-lac.vercel.app/)
- **GitHub**: [https://github.com/rishabhbhardwaj-dev](https://github.com/rishabhbhardwaj-dev)
- **LinkedIn**: [https://www.linkedin.com/in/rishabhbhardwaj-tech/](https://www.linkedin.com/in/rishabhbhardwaj-tech/)

---

## 17. License

This project is currently provided without a specified open-source license. All rights reserved.