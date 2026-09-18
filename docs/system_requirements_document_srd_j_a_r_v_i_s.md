# System Requirements Document (SRD)

**Project Name:** J.A.R.V.I.S. (Autonomous Desktop Voice Agent)  
**Document Version:** 1.0.0  
**Document Type:** System & Technical Requirements Specification  
**Status:** Approved / Architecture Baseline  

---

## 1. System Overview & Scope

The System Requirements Document (SRD) defines the low-level system design, communication protocols, hardware/software dependencies, operational threads, event-driven pipelines, security validation algorithms, and error handling mechanics for J.A.R.V.I.S.

The solution operates as a decoupled dual-service system:
* **Frontend Node:** Java 21 LTS + OpenJFX 21 rendering an Iron Man Sci-Fi HUD, handling local microphone audio capture and speaker stream playback.
* **Backend Core:** Python 3.12 running an asynchronous FastAPI WebSocket engine, local Faster-Whisper Speech-to-Text, Edge-TTS streaming, OS control automation (`pyautogui`/`pynput`/`opencv`), and an embedded SQLite database configured in WAL mode.

---

## 2. Hardware & Operating System Specifications

### 2.1 Operating System Compatibility
* **Windows:** Windows 10 (Build 19041+) and Windows 11 (64-bit).
* **Linux:** Ubuntu 22.04 LTS+, Debian 12+, Fedora 39+ (X11 native or Wayland with XWayland compatibility layer for cursor/keyboard automation).

### 2.2 Hardware Requirements

| Specification | Minimum Requirement | Recommended Production Target |
| :--- | :--- | :--- |
| **Processor (CPU)** | Quad-Core x86_64 / ARM64 (2.0 GHz) | 8-Core Intel Core i7 / AMD Ryzen 7 or Apple Silicon |
| **Memory (RAM)** | 8 GB DDR4 | 16 GB DDR4/DDR5 |
| **Storage** | 2 GB free disk space (app + models) | 10 GB SSD (NVMe preferred for fast SQLite WAL writes) |
| **Audio Peripherals** | 16-bit 44.1 kHz USB / Built-in Mic & Speaker | Dedicated noise-canceling mic array & stereo output |
| **Video Camera** | Standard 720p USB/Integrated Webcam | 1080p 30 FPS USB Video Class (UVC) Camera |
| **Network** | Offline capable (Local LLM/Piper) or 5 Mbps internet | Stable broadband connection (for Cloud LLM & Edge-TTS) |

---

## 3. Software Dependencies & Runtime Environment

### 3.1 Java Ecosystem (Presentational GUI)
* **Java Development Kit (JDK):** OpenJDK 21 LTS (Temurin / Liberica).
* **GUI Framework:** OpenJFX 21.0.2+.
* **WebSocket Client:** `Java-WebSocket` 1.5.6 or `Java.net.http.WebSocket`.
* **JSON Serializer:** Jackson Databind 2.17+ or Gson 2.10+.
* **Audio Engine:** Java Sound API (`javax.sound.sampled`) & JavaFX Media (`javafx.scene.media`).
* **Icons & Fonts:** FontAwesomeFX / Custom TTF fonts (`Orbitron`, `Rajdhani`).

### 3.2 Python Ecosystem (Agentic Backend)
* **Runtime:** Python 3.12.x (64-bit virtual environment).
* **Async Gateway:** `fastapi` 0.110+, `uvicorn[standard]` 0.29+, `websockets` 12.0+.
* **Speech-to-Text (STT):** `faster-whisper` (CTranslate2-based Whisper model: `base.en` or `small`).
* **Text-to-Speech (TTS):** `edge-tts` (dynamic neural voice) + `pygame` / `sounddevice` for fallback local audio.
* **OS Automation:** `pyautogui` 0.9.54+, `pynput` 1.7.6+.
* **Computer Vision:** `opencv-python` 4.9.0+.
* **Database Driver:** Built-in `sqlite3` driver with foreign key and WAL support.
* **LLM Client Adapters:** `openai` 1.25+, `httpx` 0.27+ (for Gemini, Anthropic, and Ollama REST calls).

---

## 4. Communication Protocol & Data Contracts (WebSocket IPC)

Communication between JavaFX (Client) and Python (Server) is strictly full-duplex over loopback TCP (`ws://127.0.0.1:8765/ws/agent`). All packets are transmitted as serialized UTF-8 JSON payloads.

```
+------------------+                    +---------------------+
|   JavaFX Client  |                    |    Python Backend   |
+------------------+                    +---------------------+
         |                                         |
         | -------- ws://127.0.0.1:8765 ---------> |  Connection Handshake
         | <------- SYSTEM_GREETING -------------- |  Trigger initial TTS greeting
         |                                         |
         | -------- USER_PROMPT (Voice/Text) ----> |  User issues command
         | <------- STATUS_UPDATE (RUNNING) ------ |  Task worker spawned
         | <------- OS_ACTION_FEEDBACK ----------- |  Action execution status
         | <------- TTS_AUDIO_STREAM ------------- |  Real-time audio response
         |                                         |
         | -------- USER_INTERRUPT (Voice) ------> |  Concurrent voice query
         | <------- TTS_AUDIO_STREAM ------------- |  Interruption addressed
         |                                         |
```

### 4.1 Client-to-Server Message Schemas

#### Schema: `USER_PROMPT`
Sent when a user speaks or submits a text command from the JavaFX console.
```json
{
  "event_type": "USER_PROMPT",
  "session_id": "9b1deb4d-3b7d-4bad-9bdd-2b0d7b3dcb6d",
  "timestamp": "2026-09-18T14:30:00Z",
  "payload": {
    "input_mode": "VOICE",
    "text_content": "Buka Chrome lalu cari berita teknologi terkini",
    "audio_sample_rate": 16000
  }
}
```

#### Schema: `SYSTEM_CONFIG_UPDATE`
Sent when updating LLM credentials or settings from the UI.
```json
{
  "event_type": "SYSTEM_CONFIG_UPDATE",
  "payload": {
    "provider_name": "openai",
    "model_name": "gpt-4o",
    "api_key": "sk-proj-...",
    "base_url": "https://api.openai.com/v1"
  }
}
```

#### Schema: `USER_ABORT_SIGNAL`
Sent when the user clicks the UI Kill-Switch or uses an emergency voice trigger.
```json
{
  "event_type": "USER_ABORT_SIGNAL",
  "payload": {
    "reason": "USER_MANUAL_TERMINATION",
    "task_id": "c84f509e-71b3-4613-a41a-8288cf3b429d"
  }
}
```

### 4.2 Server-to-Client Message Schemas

#### Schema: `SYSTEM_GREETING`
Triggered immediately upon initial application launch.
```json
{
  "event_type": "SYSTEM_GREETING",
  "payload": {
    "greeting_text": "System online. Good evening, Sir. All diagnostics optimal.",
    "audio_stream_url": "/audio/cache/greeting_01.mp3",
    "system_status": "READY"
  }
}
```

#### Schema: `ACTION_DISPATCH`
Transmits current OS execution stage to update the HUD indicators.
```json
{
  "event_type": "ACTION_DISPATCH",
  "task_id": "c84f509e-71b3-4613-a41a-8288cf3b429d",
  "payload": {
    "action_type": "TYPE",
    "target": "Active Window: Google Chrome",
    "execution_order": 2,
    "status": "IN_PROGRESS"
  }
}
```

#### Schema: `SECURITY_ALERT`
Fired when a violation triggers the kill-switch.
```json
{
  "event_type": "SECURITY_ALERT",
  "task_id": "c84f509e-71b3-4613-a41a-8288cf3b429d",
  "payload": {
    "violation_code": "PII_CREDENTIAL_DETECTED",
    "message": "Access denied. Action aborted due to security guardrail.",
    "action_taken": "TASK_TERMINATED"
  }
}
```

---

## 5. Concurrency Architecture & Threading Model

To satisfy the core requirement that **the agent can communicate while actively executing an OS task**, the Python backend implements an isolated multi-threaded and asynchronous pipeline:

```
                                 [WebSocket Event Loop (FastAPI / Asyncio)]
                                                    │
                         ┌──────────────────────────┴──────────────────────────┐
                         ▼                                                     ▼
              [Voice Manager Worker]                                [Task Orchestration Worker]
           (Thread-1: Async Event Loop)                         (Thread-2: Dedicated ThreadPool)
                         │                                                     │
        ┌────────────────┴────────────────┐                   ┌────────────────┴────────────────┐
        ▼                                 ▼                   ▼                                 ▼
[Faster-Whisper STT]              [Edge-TTS Streamer]   [PyAutoGUI Actions]           [Text Typing Loop]
(Runs without blocking)          (Pipes audio chunks)   (Mouse movements)             (Character Cadence)
        │                                 │                   │                                 │
        └─────────────────┬───────────────┘                   └────────────────┬────────────────┘
                          │                                                    │
                          │ ◄────────── CANCELLATION TOKEN ────────────────────┤
                          │  (In case of abort / emergency kill-switch)        │
                          ▼                                                    ▼
                 [JavaFX Audio Player]                              [Operating System Host]
```

### Threading Rules:
1. **Voice Isolation:** The voice reception and TTS audio generation loop never executes on the OS Automation Thread.
2. **Cancellation Token System:** The Task Worker periodically checks an `asyncio.Event` flag named `abort_requested`. If flagged, current `pyautogui` loops break immediately.
3. **JavaFX UI Thread Safety:** Incoming WebSocket payloads in Java must never mutate UI components directly; all UI updates must be wrapped inside `Platform.runLater(() -> { ... })`.

---

## 6. Security Guardrail & Sanitization Algorithms

All user prompts and model-generated execution plans pass through a mandatory pre-execution filter before any OS command is issued.

### 6.1 PII & Credential Detection Filter
* **Email Regex:** `r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+"`
* **Phone Number Regex:** `r"(\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}"`
* **Credentials/Secrets Regex:** `r"(?i)(password|passwd|secret|api[_-]?key|bearer|token)\s*[:=]\s*\S+"`
* **Financial/ID Patterns:** Credit card numbers (Luhn pattern matches) and National ID sequences.

### 6.2 OS Command Blacklist
The terminal and shell adapters forbid any execution containing the following tokens or paths:
* **Restricted Tokens:** `rm -rf`, `del /f /s /q`, `format`, `dd if=`, `mkfs`, `:(){ :|:& };:`, `chmod -R 777 /`.
* **Restricted Paths:** `C:\Windows`, `C:\Windows\System32`, `/etc`, `/boot`, `/sys`, `/proc`, `~/.ssh`.

### 6.3 Fail-Safe Logic Flow
```
                   [Target Action Plan]
                            │
                            ▼
              [Check 1: PII Regex Match?]
                 ├── YES ──> [Log to AUDIT_VIOLATIONS] ──> [Trigger Kill-Switch & Abort]
                 └── NO
                            │
                            ▼
           [Check 2: Destructive Command/Path?]
                 ├── YES ──> [Log to AUDIT_VIOLATIONS] ──> [Trigger Kill-Switch & Abort]
                 └── NO
                            │
                            ▼
              [Check 3: User Moved Mouse to Corner?]
                 ├── YES ──> [PyAutoGUI FailSafeException] ──> [Instant Terminate]
                 └── NO
                            │
                            ▼
                  [Execute Safe OS Action]
```

---

## 7. Storage Engine & Crash Resilience Architecture

### 7.1 Database Engine Configuration
* **Engine:** SQLite 3 embedded.
* **Journaling Mode:** Write-Ahead Logging (`PRAGMA journal_mode = WAL;`).
* **Synchronous Flag:** `PRAGMA synchronous = NORMAL;` (guarantees durability during OS crash while avoiding excessive disk flush overhead).
* **Busy Timeout:** `PRAGMA busy_timeout = 5000;` (prevents lock collisions between threads).

### 7.2 Session Rehydration & State Recovery
1. Upon application initialization, the Python backend executes:
   ```sql
   SELECT session_id, system_state FROM sessions ORDER BY started_at DESC LIMIT 1;
   ```
2. If `system_state == 'ONLINE'`, the prior session was terminated abnormally (e.g., power failure or crash).
3. The backend executes a recovery routine:
   * Sets the previous session's `system_state = 'CRASHED'`.
   * Queries the last 15 entries from `conversation_logs` where `session_id = :prev_session_id`.
   * Injects the recovered conversation history into the LLM context prompt buffer.
   * Creates a new session in `sessions` with `system_state = 'ONLINE'`.

---

## 8. GUI Rendering & Visual Architecture (JavaFX HUD)

### 8.1 Color Palette & Theme Tokens
* **Background Deep:** `#030b17`
* **Card/Container Surface:** `rgba(7, 21, 41, 0.75)`
* **Primary Neon Blue:** `#00d2ff`
* **Secondary Cyan Glow:** `#00f0ff`
* **Alert Red (Kill Switch):** `#ff3344`
* **Text High Contrast:** `#e6f7ff`
* **Text Muted:** `#5c8ca6`

### 8.2 Arc Reactor Component Design
The central circular reactor is rendered on a hardware-accelerated `javafx.scene.canvas.Canvas`:
* **Layer 1 (Outer Ring):** Segmented dashed circle rotating clockwise at 15 RPM using `AnimationTimer`.
* **Layer 2 (Middle Ring):** Counter-clockwise rotating notched gear track with 8 geometric teeth.
* **Layer 3 (Inner Ring):** Smooth pulsing cyan glow created with `BoxBlur` and `Glow(0.85)` effects.
* **Layer 4 (Core Text):** Dynamic status label ("J.A.R.V.I.S. - SYSTEM ONLINE").

---

## 9. Quality Attributes & Acceptance Testing Criteria

### 9.1 Verification Matrix

| Requirement ID | Test Case | Target Metric | Verification Method |
| :--- | :--- | :--- | :--- |
| **SRD-TC-01** | Proactive Voice Greeting | Audio plays < 800ms after JavaFX stage displays | Automated startup timer benchmark |
| **SRD-TC-02** | Pluggable LLM Switch | Switch from OpenAI to local Ollama via UI | Functional test without application restart |
| **SRD-TC-03** | Human-like Keystrokes | Keystroke intervals between 20ms and 60ms | Key event timestamp delta analysis |
| **SRD-TC-04** | PII Guardrail Kill-Switch | Input text containing email address | Task status transitions to `ABORTED` in < 50ms |
| **SRD-TC-05** | Persistent Context Rehydration | Kill process via `kill -9` or Task Manager | Relaunched app retains complete chat memory |
| **SRD-TC-06** | Concurrent Interruption | Speak to agent while typing task is active | Assistant answers voice query without crashing |
| **SRD-TC-07** | PyAutoGUI Fail-Safe | Manually force mouse cursor to (0,0) | Automation halts immediately |

---

## 10. Project Directory Blueprint

```
jarvis-system/
├── frontend-javafx/
│   ├── pom.xml (Maven Build Configuration)
│   └── src/main/
│       ├── java/com/jarvis/hud/
│       │   ├── App.java (JavaFX Application Entry)
│       │   ├── controller/
│       │   │   ├── HUDController.java
│       │   │   └── SettingsController.java
│       │   ├── websocket/
│       │   │   ├── JarvisWebSocketClient.java
│       │   │   └── PacketListener.java
│       │   ├── audio/
│       │   │   ├── AudioCaptureService.java
│       │   │   └── AudioPlaybackService.java
│       │   └── view/
│       │       └── ArcReactorCanvas.java
│       └── resources/
│           ├── fxml/hud_main.fxml
│           ├── css/jarvis_hud.css
│           ├── fonts/Orbitron-Bold.ttf
│           └── assets/ironman_core.svg
│
└── backend-python/
    ├── requirements.txt
    ├── main.py (FastAPI Gateway & WebSocket Server)
    ├── config.py (Settings & Environment Loader)
    ├── memory/
    │   ├── db_manager.py (SQLite WAL Connection Manager)
    │   └── schema.sql (Production DDL)
    ├── guardrails/
    │   ├── pii_scanner.py (Regex & Sensitive Pattern Filter)
    │   └── os_protection.py (Command Blacklist & Path Checker)
    ├── engine/
    │   ├── llm_factory.py (Pluggable Provider Adapter)
    │   ├── voice_service.py (Faster-Whisper & Edge-TTS)
    │   └── os_controller.py (PyAutoGUI, Keystrokes, OpenCV)
    └── data/
        └── jarvis_memory.db (Persistent Storage)
```