# Product Requirement Document (PRD)
**Project Name:** J.A.R.V.I.S. (Autonomous Desktop Voice Agent)  
**Version:** 1.0.0  
**Document Status:** Approved / Ready for Development  
**Target OS:** Windows 10/11 & Linux (X11/Wayland compatible)  

---

## 1. Executive Summary & Vision
J.A.R.V.I.S. is an agentic, voice-controlled desktop assistant engineered to manage and automate operating system workflows autonomously while maintaining safety guardrails. The system couples an Iron Man-inspired Heads-Up Display (HUD) built in JavaFX with an asynchronous Python backend orchestrating automated screen navigation, speech processing, and pluggable Large Language Model (LLM) providers.

### Primary Objectives
* **Hands-free Interaction:** Deliver proactive greetings and dynamic text-to-speech audio feedback.
* **Autonomous Execution:** Perform operating system interactions (cursor motion, keyboard typing, camera triggers, application launch) per user instructions.
* **Resilient Context Store:** Maintain persistent, crash-safe local context storage.
* **Strict Security Guardrails:** Prevent unauthorized access to personally identifiable information (PII), credentials, or operating system destruction.
* **Non-blocking Concurrency:** Ensure uninterrupted voice communication even while background OS tasks are executing.

---

## 2. System Architecture & Tech Stack

The architecture follows a decoupled Client-Server model connected via local WebSockets:

```
┌────────────────────────────────────────────────────────┐
│               PRESENTATIONAL LAYER                     │
│  Java 21 LTS + JavaFX 21 + FXML / Custom CSS           │
│  - Futuristic Sci-Fi HUD Canvas & Neon Visualizers     │
│  - Audio Microphone Capture & Speaker Output Stream    │
└─────────────────────────▲──────────────────────────────┘
                          │ (Bi-directional WebSocket IPC: Port 8765)
┌─────────────────────────▼──────────────────────────────┐
│              ORCHESTRATION GATEWAY                     │
│  Python 3.12 (FastAPI + Asyncio)                       │
│  - Audio Event Routing & Multi-threaded Task Workers   │
│  - Pluggable LLM Adapter Interface                     │
└─────────────────────────▲──────────────────────────────┘
                          │
         ┌────────────────┴────────────────┐
         ▼                                 ▼
┌─────────────────────────┐       ┌─────────────────────────┐
│   AGENTIC OS CONTROL    │       │     LOCAL MEMORY        │
│  - PyAutoGUI / Pynput   │       │  SQLite 3 (WAL Mode)    │
│  - OpenCV (Webcam)      │       │  - ACID Event Logging   │
│  - Security Guardrail   │       │  - Zero Data Corruption │
└─────────────────────────┘       └─────────────────────────┘
```

### Component Details
1. **Frontend (GUI):** Java 21 LTS, OpenJFX 21, ControlsFX, Canvas 2D engine.
2. **Backend Engine:** Python 3.12, FastAPI, WebSockets, Asyncio.
3. **Voice Engine:** `faster-whisper` (local Speech-to-Text) and `edge-tts` (low-latency Text-to-Speech).
4. **OS Automation:** `pyautogui`, `pynput`, `opencv-python`.
5. **Database:** Embedded SQLite 3 with Write-Ahead Logging (`PRAGMA journal_mode=WAL`).

---

## 3. Functional Requirements (FR)

### FR-01: Proactive Audio Greeting & Voice Feedback
* **Trigger:** Initial handshake between JavaFX client and Python server.
* **Behavior:** The system plays an audible greeting according to the local timestamp (e.g., *"System online. Good morning, Sir."*).
* **Execution Feedback:** Every action or status change must produce simultaneous voice feedback (TTS) and HUD visual state updates.

### FR-02: Futuristic HUD Interface
* **Aesthetics:** Deep space blue background (`#030b17`) with cyan/neon accents (`#00d2ff`, `#00f0ff`) and drop-shadow glow effects.
* **Core Elements:**
  * Animated central Arc Reactor (concentric rotating loops rendered on a JavaFX Canvas).
  * Real-time audio waveform visualizer tied to mic input.
  * System telemetry monitors (CPU, RAM, Disk, Network).
  * Quick-access application triggers and interactive command input bar.

### FR-03: Pluggable Multi-Provider LLM Engine
* **Architecture:** Strategy/Adapter Pattern for language models.
* **Supported Integrations:**
  * Cloud Providers: OpenAI (GPT-4o), Google Gemini, Anthropic Claude.
  * Local Self-Hosted: Ollama, vLLM, LM Studio (OpenAI-compatible endpoint).
* **Configuration:** Dedicated Settings modal in JavaFX allowing manual API Key injection, base URL definition, and model selection.

### FR-04: Full OS Navigation & Human-like Typing
* **Cursor Control:** Relative and absolute mouse movements, left/right/double click, dragging, and scrolling.
* **Keyboard Automation:** Automated text entry across active input fields, supporting dynamic speed intervals (0.02s – 0.06s per keystroke) to simulate natural cadence and avoid input buffer truncation.
* **Peripherals:** Programmatic webcam access via OpenCV for vision-assisted actions upon explicit instruction.

### FR-05: Real-time Persistent Context Memory
* **Storage Engine:** SQLite 3 utilizing WAL (Write-Ahead Logging) mode.
* **Durability:** Every interaction, task state, and extracted context parameter is written to disk immediately with ACID guarantees.
* **Recovery:** Upon unexpected hardware shutdown or restart, the system must reload previous conversation history, user preferences, and pending tasks without manual re-entry.

### FR-06: Full-Duplex Concurrency
* **Threading Model:** Separation of concerns using two isolated workers:
  * `VoiceWorkerThread`: Dedicated to continuous audio input stream listening and real-time TTS output.
  * `TaskExecutionWorker`: Asynchronous task execution pipeline for OS actions.
* **Interactivity:** Users can query the assistant, issue corrections, or ask general questions while the OS task is actively manipulating windows or typing.

---

## 4. Security Guardrails & Safety Constraints

To mitigate risks inherent to agentic computer automation, the system enforces non-negotiable security boundaries:

| ID | Constraint | Enforcement Mechanism |
| :--- | :--- | :--- |
| **SEC-01** | Strict PII & Credential Protection | Regex and entity-recognition guardrails validate all text outputs prior to typing or disk storage. Matches for passwords, credentials, email patterns, phone numbers, and home addresses are blocked. |
| **SEC-02** | OS Integrity & Anti-Destruction | Hardcoded command blacklist prevents dangerous shell commands (`rm`, `del`, `format`, `dd`) and access to restricted paths (`/etc`, `/boot`, `C:\Windows\System32`). |
| **SEC-03** | Autonomous Action Restriction | Purely event-driven execution. No autonomous OS interaction may commence without an explicit user command (voice or text trigger). |
| **SEC-04** | Instant Task Abort (Kill Switch) | If an instruction violates SEC-01 or SEC-02, the task worker terminates immediately (`SIGINT`/Task Cancellation), announces an audible alert (*"Access denied. Task aborted due to safety protocols."*), and logs the incident. |
| **SEC-05** | Hardware Fail-Safe | `pyautogui.FAILSAFE = True` is permanently enabled. If the user forcibly moves the physical mouse cursor to any screen corner, automation halts instantly. |

---

## 5. Non-Functional Requirements (NFR)

* **Latency:** Voice feedback round-trip time (STT -> LLM response -> First TTS chunk) must target under 1.5 seconds for cloud models and under 1.0 second for local edge models.
* **Resource Consumption:** JavaFX GUI baseline memory usage must remain under 300MB RAM during idle monitoring.
* **Reliability:** Background disconnects between JavaFX and Python must auto-reconnect with exponential backoff (1s, 2s, 4s, up to 10s).
* **Portability:** File system operations and path resolutions must use platform-agnostic abstractions (`pathlib.Path` in Python, `java.nio.file.Path` in Java).

---

## 6. Implementation Roadmap

```
Phase 1: Foundation & IPC
├── Setup JavaFX 21 skeleton with HUD layouts
├── Build FastAPI WebSocket server in Python 3.12
└── Establish bi-directional JSON messaging protocol

Phase 2: Voice & LLM Integration
├── Implement Edge-TTS audio stream generation
├── Configure faster-whisper local STT pipeline
└── Implement Pluggable LLM Adapter (OpenAI / Ollama / Gemini)

Phase 3: Persistent Storage & Safety Guardrails
├── Initialize SQLite schema with WAL configuration
├── Integrate TextSecurityGuardrail & Command Blacklist
└── Validate crash recovery and state rehydration

Phase 4: OS Automation & Agentic Capabilities
├── Implement OSController (Mouse, Keystrokes, Window focus)
├── Implement Human-like typing engine with random jitter
└── Connect OpenCV module for controlled camera snapshots

Phase 5: Concurrency & End-to-End Hardening
├── Implement asyncio Task Cancellation tokens for voice interrupts
├── Full UI styling (Canvas Arc Reactor, Glow effects, Audio visualizer)
└── Integration tests on Windows and Linux distributions
```