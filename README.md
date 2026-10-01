# JARVIS AI — Always-On Neural Interface

> "Sometimes you gotta run before you can walk." — Tony Stark

A voice-activated AI desktop assistant powered by **Groq AI and Llama models**, featuring a live 3D neural orb dashboard, real-time state synchronization, screen awareness, smart web and person lookup, natural-language command processing, and desktop automation.

![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-2.x-000000?style=flat&logo=flask&logoColor=white)
![Groq](https://img.shields.io/badge/Groq-AI-F55036?style=flat)
![Three.js](https://img.shields.io/badge/Three.js-3D-black?style=flat&logo=three.js)
![Windows](https://img.shields.io/badge/Platform-Windows-0078D6?style=flat&logo=windows)

---

## Features

| Feature | Description |
|---|---|
| **Always-On Wake Word** | Say "Hey Jarvis" to activate the assistant without pressing a button. |
| **Groq AI Brain** | Uses Groq-hosted Llama models for natural-language interaction and AI responses. |
| **Real-Time Dashboard** | Interactive Three.js neural orb synchronized with assistant states. |
| **Chat Interface** | Displays user and JARVIS conversations directly in the dashboard. |
| **SSE Live Sync** | Server-Sent Events keep voice, responses, and UI state synchronized in real time. |
| **Smart Commands** | Natural-language commands can trigger web searches, application launches, and other actions. |
| **Screen Awareness** | Captures and analyzes the current screen using Groq vision capabilities. |
| **Barge-In / Interrupt** | Saying "Hey Jarvis" while JARVIS is speaking can interrupt the current response. |
| **Person Lookup** | Searches for people and provides information through web resources and AI responses. |
| **Smart Image Search** | Opens image search results for requested people or subjects. |
| **Instagram Finder** | Searches for Instagram profiles through natural-language commands. |
| **Sleep / Wake Mode** | Put JARVIS into sleep mode and wake it again using voice commands. |
| **AI File Save** | AI-generated responses can be saved to files. |
| **System Monitoring** | Displays CPU and RAM usage on the dashboard. |
| **Hot Restart** | Restart JARVIS through a voice command without manually restarting the application. |

---

## Architecture

JARVIS follows an event-driven architecture where voice or text input is interpreted, routed to the appropriate execution path, and synchronized with the browser dashboard through Flask and Server-Sent Events.

```text
                         USER
                          |
                          v
                +--------------------+
                | Voice / Text Input |
                +---------+----------+
                          |
                          v
                +--------------------+
                | Speech Recognition |
                | Command Processing |
                +---------+----------+
                          |
                          v
                +--------------------+
                | Intent / Command   |
                |     Handling       |
                +---------+----------+
                          |
             +------------+------------+
             |            |            |
             v            v            v
      +-----------+ +-----------+ +-------------+
      |  System   | | Web /     | |   Groq AI   |
      |  Actions  | | Search    | | Llama/Vision|
      +-----------+ +-----------+ +-------------+
             |            |            |
             +------------+------------+
                          |
                          v
                +--------------------+
                | Action / Response  |
                |   State Updates    |
                +---------+----------+
                          |
                          | SSE
                          v
                +--------------------+
                |   Flask Server     |
                |  API + SSE Stream  |
                +---------+----------+
                          |
                          | HTTP / SSE
                          v
                +--------------------+
                | Browser Dashboard  |
                |                    |
                | Three.js Neural Orb|
                | Chat Interface     |
                | Status Display     |
                | System Statistics  |
                +--------------------+
```

### Core Components

- **Voice Layer** — listens for the wake word and captures spoken commands.
- **Command Processing** — interprets natural-language requests and determines the appropriate action.
- **System Integration** — handles desktop applications, browser actions, system information, and other local operations.
- **Groq AI Layer** — handles conversational AI requests and screen-analysis tasks using supported Llama models.
- **Flask Backend** — provides the local application server and API endpoints.
- **SSE Communication** — streams assistant states, messages, and events to the browser in real time.
- **Three.js Dashboard** — provides the visual interface, neural orb, chat display, status information, and system statistics.

---

## How It Works

JARVIS converts a voice command into an action or AI response through the following flow:

```text
User speaks
    |
    v
Wake-word / Speech Recognition
    |
    v
Command Processing
    |
    +---------------------+
    |                     |
    v                     v
System / Web Action     AI Request
    |                     |
    |                     v
    |                Groq AI / Vision
    |                     |
    +----------+----------+
               |
               v
        Action / Response
               |
               v
          SSE Stream
               |
        +------+------+
        |             |
        v             v
    Dashboard       Voice
```

### Core Flow

1. **Voice Input** — JARVIS listens for the wake word `"Hey Jarvis"`.
2. **Speech Recognition** — the spoken command is converted into text.
3. **Command Processing** — JARVIS determines what type of request was made.
4. **Execution** — the appropriate system, web, or application action is performed.
5. **AI Processing** — AI requests are handled using Groq-hosted Llama models, including vision capabilities where applicable.
6. **Real-Time Updates** — Server-Sent Events synchronize the browser dashboard with assistant states and responses.
7. **Response** — JARVIS provides feedback through the dashboard and voice output.

---

## Tech Stack

### AI & Backend

- **Python 3.11+**
- **Flask**
- **Groq API**
- **Llama Models**
- **pyttsx3**
- **Speech Recognition**

### Frontend

- **HTML5**
- **CSS3**
- **JavaScript**
- **Three.js**
- **WebGL**

### Communication

- **HTTP**
- **Server-Sent Events (SSE)**

### Platform

- **Windows**

---

## Quick Start

### Prerequisites

- Python 3.11+
- Windows
- Working microphone
- Groq API key
- Internet connection for AI and web-based features

### 1. Clone the repository

```bash
git clone https://github.com/rishabhbhardwaj-dev/Jarvis-voice-assistant.git
cd Jarvis-voice-assistant
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

If PyAudio installation fails, try:

```bash
pip install pipwin
pipwin install pyaudio
```

### 3. Configure the Groq API key

Configure your Groq API key using the configuration expected by `config.py`.

**Do not commit your real API key to GitHub.**

### 4. Launch JARVIS

```bash
python main.py
```

Or launch it using:

```text
run_jarvis.bat
```

The dashboard runs locally at:

```text
http://localhost:5000
```

---

## Voice Command Reference

### Wake & Control

| Say | Action |
|---|---|
| `"Hey Jarvis"` | Wake up JARVIS |
| `"Jarvis sleep"` | Enter sleep mode |
| `"Wake up Jarvis"` | Resume from sleep mode |
| `"Jarvis restart"` | Restart JARVIS |
| `"Jarvis quit"` | Shut down JARVIS |

### Web Commands

| Say | Action |
|---|---|
| `"Open YouTube"` | Opens YouTube |
| `"Search YouTube for lofi music"` | Searches YouTube |
| `"Search Google for AI news"` | Performs a Google search |
| `"Find React hooks on GitHub"` | Searches GitHub |
| `"Look up quantum physics on Wikipedia"` | Searches Wikipedia |

### Person & Entity Lookup

| Say | Action |
|---|---|
| `"Who is Rohit Sharma?"` | Opens relevant information and provides an AI response |
| `"Tell me about Elon Musk"` | Searches for information and provides a response |
| `"Show me a picture of Virat Kohli"` | Opens image search results |
| `"Photo of Cristiano Ronaldo"` | Opens image search results |
| `"Rohit Sharma Instagram"` | Searches for the relevant Instagram profile |

### System Commands

| Say | Action |
|---|---|
| `"What time is it"` | Provides the current time |
| `"What's the date"` | Provides the current date |
| `"System status"` | Shows CPU and RAM usage |
| `"Open Notepad"` | Launches Notepad |
| `"Open Calculator"` | Launches Calculator |
| `"Open VS Code"` | Launches VS Code |
| `"Play music"` | Plays local music files |

### AI Features

| Say | Action |
|---|---|
| `"What's on my screen?"` | Analyzes the current screen using Groq vision capabilities |
| `"Analyze my screen"` | Performs screen analysis |
| `"Use AI to write a cover letter"` | Generates an AI response that can be saved to a file |
| `"Reset chat"` | Clears conversation context |
| Any other supported question | Interacts with Groq AI |

---

## Project Structure

```text
JARVIS AI/
│
├── demo/
│   ├── Jarvis_SleepMode.mp4
│   └── ...
│
├── frontend/
│   ├── index.html
│   ├── script.js
│   └── style.css
│
├── screenshots/
│   ├── Jarvis_Interface(Dashboard).png
│   └── Voice Command Execution.png
│
├── .env
├── .gitignore
├── config.py
├── main.py
├── requirements.txt
├── run_jarvis.bat
└── README.md
```

> `.env` contains local configuration and should not contain credentials that are committed to the repository.

---

## Troubleshooting

| Problem | Possible Fix |
|---|---|
| Microphone not working | Set the correct microphone as the default Windows input device. |
| PyAudio installation error | Try `pip install pipwin` followed by `pipwin install pyaudio`. |
| Groq API key error | Verify the API key configuration used by `config.py`. |
| Screen awareness fails | Verify the required screen-capture dependencies are installed. |
| Port 5000 is already in use | Stop the process using port 5000 or change the application port. |
| JARVIS keeps speaking | Use the wake word to trigger the interrupt/barging-in behavior. |

---

## Demo

A typical demonstration can include:

1. Start JARVIS with `python main.py`.
2. Say **"Hey Jarvis"** to activate the assistant.
3. Ask **"What time is it"** and observe the voice and dashboard response.
4. Ask JARVIS to search YouTube for something.
5. Ask a person-related question and observe the web/AI response.
6. Ask **"What's on my screen?"** to demonstrate screen awareness.
7. Interrupt an active response using the wake word.
8. Say **"Jarvis sleep"** and observe the dashboard state.
9. Say **"Wake up Jarvis"** to restore the assistant.
10. Use the dashboard chat input for a text-based interaction.
11. Say **"Jarvis quit"** to shut down the application.

---

## Screenshots

### JARVIS Dashboard

![JARVIS Dashboard](./screenshots/Jarvis_Interface(Dashboard).png)

### Voice Command Execution

![Voice Command Execution](./screenshots/Voice%20Command%20Execution.png)

---

## Author

**Rishabh Bhardwaj**

- Portfolio: https://rishabh-portfolio-lac.vercel.app/
- GitHub: https://github.com/rishabhbhardwaj-dev
- LinkedIn: https://www.linkedin.com/in/rishabhbhardwaj-tech/

---

## License

No open-source license has been specified for this project.

---

Built with Python, Flask, Groq AI, Llama models, and Three.js.