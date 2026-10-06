# JARVIS AI — Refinement & Modernization Architecture Progress

**Project Name**: JARVIS AI — Agentic Multimodal Desktop AI Assistant  
**Purpose**: Single Source of Truth for ongoing refinement, modularization, and agentic modernization of JARVIS AI  
**Current Status**: Phase 1 Completed & Verified (Runtime Isolated)  
**Last Updated**: October 6, 2026  
**Current Phase**: Phase 1 — Tool Registry Foundation  
**Next Planned Phase**: Phase 2 — Incremental Tool Migration  

---

## 1. PROJECT CONTEXT

JARVIS is a fully functional Python desktop voice assistant featuring:

*   **Voice Interaction**: Mic capture via `speech_recognition` (Google Speech STT).
*   **Wake-Word Detection**: Always-on background thread listening for `"Hey Jarvis"` / `"Jarvis"`.
*   **Barge-In / Interruption**: Instant TTS process termination (`stop_speaking()`) upon new wake-word or user input.
*   **Text-to-Speech (TTS)**: Non-blocking, interruptible Windows PowerShell `System.Speech.Synthesis.SpeechSynthesizer`.
*   **Groq AI Engine**: Fast natural-language conversational responses using Groq API.
*   **Screen Awareness**: Base64 screenshot capture (`pyautogui`) analyzed by Groq Vision model.
*   **Flask & SSE Backend**: HTTP routing and live Server-Sent Events (`broadcast()`) for state sync.
*   **Three.js Neural Orb Dashboard**: Real-time cyberpunk 3D orb visualizer reacting to voice states (`WAITING`, `WAKE`, `LISTENING`, `PROCESSING`, `SPEAKING`, `SLEEP`).
*   **System & Browser Control**: Deterministic app launching, website/search triggers, person lookup, CPU/RAM monitoring, and file save routines.

### Core Objective

**The goal is NOT to rebuild JARVIS from scratch.**

The objective is to incrementally evolve the existing working JARVIS codebase into a highly capable **Agentic Multimodal Desktop AI Assistant**, while strictly preserving the current working voice user experience, Neural Orb UI, and system capabilities.

---

## 2. CURRENT ARCHITECTURE

```text
User Input (Voice / Web UI)
           ↓
    Flask / main.py
           ↓
Command Handling / Groq LLM
           ↓
System Actions / AI Response
           ↓
   SSE Broadcast (broadcast)
           ↓
 Three.js Neural Orb Dashboard
           ↓
PowerShell TTS / User Audio
```

### Architectural Reality Check:

*   **[`main.py`](file:///d:/Dekstop/JARVIS%20AI/main.py)** remains the central backend orchestrator handling Flask, SSE broadcasting, `VoiceEngine`, PowerShell TTS, and command routing.
*   Command dispatching is currently performed via deterministic keyword/regex matching inside `execute_system_command()`.
*   The **Tool Registry** ([`tools/`](file:///d:/Dekstop/JARVIS%20AI/tools/)) has been constructed as an isolated package foundation, but is **NOT yet connected to `main.py`**.
*   Voice handling, TTS, SSE streaming, Flask routes, Three.js Neural Orb visualizer, and Groq configuration remain 100% untouched and functional.

---

## 3. COMPLETED WORK

### Phase 0 — Architectural Inspection
*   **Status**: `COMPLETED`
*   **Summary**: A thorough read-only audit of the entire codebase was conducted.
*   **Findings**:
    *   Monolithic structure in `main.py`.
    *   Hardcoded command dispatcher without formal tool abstraction.
    *   Absence of a multi-step planner/executor/verifier architecture.
    *   Absence of persistent memory and structured permissions/security boundaries.
    *   Opportunity to introduce a modular Tool Registry and Groq LLM function calling incrementally without breaking existing features.
*   **Conclusion**: `GO WITH CONDITIONS` (Protect existing voice/TTS/UI runtime; migrate incrementally).

---

### Phase 1 — Tool Registry Foundation
*   **Status**: `COMPLETED`
*   **Files Created**:
    ```text
    tools/
    ├── __init__.py
    ├── base.py
    └── registry.py
    ```
*   **Component Details**:
    *   **[`tools/base.py`](file:///d:/Dekstop/JARVIS%20AI/tools/base.py)**: Provides `BaseTool` abstract class containing `name`, `description`, `parameters` (JSON Schema), abstract `execute()`, and `to_groq_schema()` for OpenAI/Groq compatible schema generation.
    *   **[`tools/registry.py`](file:///d:/Dekstop/JARVIS%20AI/tools/registry.py)**: Provides `ToolRegistry` container supporting `register()`, `get()`, `list_tools()`, `get_schemas()`, safe `execute()`, and error boundary handling.
    *   **[`tools/__init__.py`](file:///d:/Dekstop/JARVIS%20AI/tools/__init__.py)**: Exposes `BaseTool`, `ToolRegistry`, and default global `registry` instance.
*   **Isolation Guarantee**: Created as an isolated foundation. No imports or modifications were made to `main.py` or any active JARVIS runtime file.

---

## 4. PHASE 1 VALIDATION

The following empirical verification steps were successfully executed:

1. **Import Integrity**: `BaseTool`, `ToolRegistry`, and `registry` imported without errors.
2. **Tool Registration**: Registered a dummy `CalculatorTool` subclass.
3. **Retrieval & Listing**: `get('calculator')` returned the instance; `list_tools()` listed `'calculator'`.
4. **Schema Generation**: `get_schemas()` output valid OpenAI/Groq function calling payload format.
5. **Tool Execution**: `execute('calculator', a=10, b=5, operation='add')` returned `"Result: 15"`.
6. **Error Boundary**: `execute('nonexistent_tool')` returned `"[ERROR] Tool 'nonexistent_tool' is not registered."` without crashing.
7. **Runtime Isolation**: **`main.py` does not currently import or use the Tool Registry.**

### Post-Phase 1 Runtime Verification:
*   JARVIS process started normally (`python main.py`).
*   Existing voice input and wake word (`"Hey Jarvis"`) responded as expected.
*   PowerShell TTS speech and barge-in functioned properly.
*   SSE stream and Three.js Neural Orb state transitions (`cyan` / `green` / `dim`) operated normally.

**Status**: `PHASE 1 = SAFE AND VERIFIED`

---

## 5. PROTECTED / DO NOT BREAK

The following components are strictly protected and must NOT be altered or broken during future refinement phases without explicit approval:

*   **`VoiceEngine`**: Always-on thread, microphone lock handling, energy thresholds.
*   **Wake-Word Detection**: `"Hey Jarvis"` pattern matching and wake state logic.
*   **Barge-In / Interruption**: Instant TTS process killing via `stop_speaking()`.
*   **SpeechRecognition**: Google Speech API microphone listener.
*   **PowerShell TTS**: Asynchronous, interruptible `System.Speech.Synthesis` speech engine.
*   **Flask Runtime & Server**: Routing, port 5000 binding, and thread pool structure.
*   **SSE Broadcast Engine**: `broadcast()` queue management and client connection tracking.
*   **Three.js Neural Orb Dashboard**: `frontend/index.html`, `script.js`, and `style.css` HUD visualizer.
*   **Groq API Configuration**: Environment variables and client setup in `config.py` / `.env`.
*   **Existing Commands & Screen Awareness**: App launching, web opening, screen analysis, AI save.

---

## 6. REFINEMENT ROADMAP

```text
Phase 0: Inspection (COMPLETED)
   ↓
Phase 1: Tool Registry Foundation (COMPLETED)
   ↓
Phase 2: Incremental Tool Migration (PLANNED)
   ↓
Phase 3: LLM Tool Calling Layer (PLANNED)
   ↓
Phase 4: Agent Runtime — Planner / Executor / Verifier (PLANNED)
   ↓
Phase 5: Persistent Memory System (PLANNED)
   ↓
Phase 6: Security & Permission Policy Layer (PLANNED)
   ↓
Phase 7: Advanced Vision & Screen Action Engine (PLANNED)
   ↓
Phase 8: Background Task & Async Job Engine (PLANNED)
   ↓
Phase 9: Browser & Desktop Computer Automation (FUTURE)
```

---

## 7. PHASE 2 — INCREMENTAL TOOL MIGRATION

*   **Status**: `PLANNED` (Next Phase)
*   **Goal**: Wrap existing hardcoded system capabilities into dedicated `BaseTool` subclasses within `tools/` and connect them to `ToolRegistry`.

### Staged Migration Order:

*   **Stage 2A (Low Risk)**:
    *   `TimeDateTool` (System clock and date formatting)
    *   `SystemStatusTool` (`psutil` CPU & RAM monitoring)
*   **Stage 2B (Medium Risk)**:
    *   `AppLauncherTool` (Windows executable launcher)
    *   `WebBrowserTool` (URL opener, search term extractor, person lookup)
    *   `AISaveTool` (Text output file save to `JarvisAI_Saves/`)
*   **Stage 2C (High Risk / Complex)**:
    *   `ScreenAwarenessTool` (Screen capture + Groq Vision API)
    *   `MusicPlayerTool` (Local music directory scanner and launcher)

> [!IMPORTANT]
> **Migration Rule**: Migrate **one capability at a time**. After every stage, launch JARVIS, test voice interaction, TTS, SSE, Neural Orb, and existing fallback behavior to ensure zero regression. Keep existing deterministic keyword matching active as a primary or fallback layer.

---

## 8. PHASE 3 — TOOL CALLING LAYER

*   **Status**: `PLANNED`
*   **Goal**: Introduce Groq LLM function/tool calling schemas.

### Target Flow:
```text
User Request
     ↓
Groq API (with tools schema payload)
     ↓
Tool Selection (or conversational text)
     ↓
ToolRegistry Execution
     ↓
Result Output
     ↓
Response Synthesizer → PowerShell TTS + SSE / Neural Orb
```

*   **Key Principles**:
    *   Tool calling is an optional enhancement layer; plain conversational queries will still return direct text.
    *   Deterministic keyword routing remains available as a fast-path fallback.

---

## 9. PHASE 4 — AGENT RUNTIME

*   **Status**: `PLANNED`
*   **Goal**: Enable multi-step task planning and execution.

### Proposed Architecture:
```text
agent/
├── runtime.py     # Agent loop orchestrator
├── planner.py     # Decomposes user goals into step-by-step tool plans
├── executor.py    # Sequential tool invocation and context tracking
├── verifier.py    # Checks if output satisfies user objective
└── state.py       # Agent task state container
```

---

## 10. PHASE 5 — PERSISTENT MEMORY SYSTEM

*   **Status**: `PLANNED`
*   **Goal**: Provide short-term conversation context and long-term user facts memory.

### Proposed Architecture:
```text
memory/
├── store.py       # SQLite database persistence interface
├── models.py      # Data schemas (Fact, Session, TaskHistory)
├── retrieval.py   # Context search & keyword retrieval
└── manager.py     # Memory ingestion & pruning controller
```

---

## 11. PHASE 6 — SECURITY AND PERMISSIONS

*   **Status**: `PLANNED`
*   **Goal**: Enforce authorization boundaries before executing high-impact system commands.

### Permission Levels:
*   `SAFE`: Read-only queries (time, date, system metrics, web searches, opening common apps).
*   `CONFIRM`: State-changing or filesystem operations (file deletion, process termination, file writing).
*   `RESTRICTED`: System-level scripts, credential access, elevated administration.

---

## 12. PHASE 7 — ADVANCED VISION & SCREEN ACTION ENGINE

*   **Status**: `PLANNED`
*   **Goal**: Evolve screen awareness from static image descriptions to element detection and desktop interaction.

```text
Screen Capture → Vision Model → UI Element Detection → Action Selection → Tool Execution → Verification
```

---

## 13. PHASE 8 — BACKGROUND TASKS & ASYNC JOBS

*   **Status**: `PLANNED`
*   **Goal**: Support non-blocking background task execution, progress monitoring, notifications, and scheduled jobs.

---

## 14. PHASE 9 — BROWSER / COMPUTER AUTOMATION

*   **Status**: `FUTURE`
*   **Goal**: Playwright integration and direct web element interaction for complex multi-site workflows.

---

## 15. RELIABILITY AND OBSERVABILITY

Key infrastructure standards to implement across all future phases:
*   Structured logging across all `tools/` and `agent/` modules.
*   Error boundaries preventing tool exceptions from stopping the voice engine.
*   Automated regression test suite covering tool registration, execution, and schema generation.

---

## 16. OPTIONAL FUTURE MODERNIZATION (NON-PRIORITY)

The following items are optional secondary ideas and must **NOT** displace core agentic development:
*   FastAPI migration
*   React frontend migration
*   Whisper / local STT integration
*   Docker containerization
*   MCP (Model Context Protocol) integration

---

## 17. CURRENT PRIORITY MATRIX

| Priority | Area | Status |
|---|---|---|
| **P0** | Architectural Inspection | `COMPLETED` |
| **P0** | Tool Registry Foundation | `COMPLETED` |
| **P0** | Phase 1 Runtime Verification | `COMPLETED` |
| **P0** | Incremental Tool Migration (Stage 2A/2B/2C) | **NEXT PLANNED** |
| **P1** | Groq Tool/Function Calling Layer | `PLANNED` |
| **P1** | Agent Runtime (Planner / Executor / Verifier) | `PLANNED` |
| **P1** | Security & Permission Policy Layer | `PLANNED` |
| **P2** | Persistent Memory (SQLite) | `PLANNED` |
| **P2** | Advanced Vision & UI Action Engine | `PLANNED` |
| **P2** | Background Task Manager | `PLANNED` |
| **P3** | Browser Automation (Playwright) | `FUTURE` |
| **P3** | FastAPI / React / Docker / MCP | `OPTIONAL FUTURE` |

---

## 18. JARVIS REFINEMENT RULES

1. **Do not rewrite JARVIS unnecessarily.**
2. **Do not replace working components merely because newer frameworks exist.**
3. **Make all architectural changes incrementally.**
4. **Implement one sub-phase at a time.**
5. **Test runtime stability after every change.**
6. **Preserve the voice-first user experience at all costs.**
7. **Preserve the Neural Orb HUD UI.**
8. **Keep deterministic keyword fallbacks during tool migration.**
9. **Never introduce complex frameworks without explicit technical justification.**
10. **Prioritize runtime reliability over feature bloat.**
11. **Maintain strong modularity (`tools/`, `agent/`, `memory/`).**
12. **Enforce security confirmation for destructive actions.**
13. **Do not claim a capability is functional until empirically validated.**
14. **Keep code clean, professional, and portfolio-ready.**
15. **Protect working features (`VoiceEngine`, TTS, SSE, Groq).**

---

## 19. PROGRESS TRACKER

- [x] Architectural inspection (Phase 0)
- [x] Tool Registry foundation (`tools/base.py`, `tools/registry.py`, `tools/__init__.py`) (Phase 1)
- [x] Runtime regression check after Phase 1
- [ ] Stage 2A: Time/Date & System Status Tool migration
- [ ] Stage 2B: App Launcher, Web Browser & AI Save Tool migration
- [ ] Stage 2C: Screen Vision & Music Tool migration
- [ ] Full `main.py` Tool Registry integration
- [ ] Groq Tool Calling integration (Phase 3)
- [ ] Agent Runtime (Planner, Executor, Verifier) (Phase 4)
- [ ] Persistent Memory System (Phase 5)
- [ ] Security & Permissions Layer (Phase 6)
- [ ] Advanced Vision Engine (Phase 7)
- [ ] Background Task Engine (Phase 8)
- [ ] Browser Automation Engine (Phase 9)

---

## 20. CORE ARCHITECTURAL PRINCIPLE

> **JARVIS is not being rebuilt.**  
> **JARVIS is being evolved incrementally from a working voice assistant into an agentic desktop AI system.**

The current working experience is our baseline. Every future phase must preserve that baseline.
