# J.A.R.V.I.S. (Just A Rather Very Intelligent System)
## Complete Technical Documentation & Operational Manual (English)

---

### Table of Contents
1. [Overview & Vision](#1-overview--vision)
2. [System Architecture](#2-system-architecture)
3. [Linux Setup & Installation Guide](#3-linux-setup--installation-guide)
   - [Linux Prerequisites](#linux-prerequisites)
   - [Automated Build & Install (Recommended)](#automated-build--install-recommended)
   - [Global `jarvis` CLI Command](#global-jarvis-cli-command)
   - [Manual Step-by-Step Execution](#manual-step-by-step-execution)
   - [Linux Troubleshooting](#linux-troubleshooting)
4. [Windows (x64) Setup & Installation Guide](#4-windows-x64-setup--installation-guide)
   - [Windows Prerequisites](#windows-prerequisites)
   - [Fast Setup via ZIP Distribution (`jarvis-windows-x64.zip`)](#fast-setup-via-zip-distribution-jarvis-windows-x64zip)
   - [Native Windows PE Launchers (`JARVIS.exe` & `JARVIS_Config.exe`)](#native-windows-pe-launchers-jarvisexe--jarvis_configexe)
   - [Manual Windows Installation](#manual-windows-installation)
   - [Windows Troubleshooting](#windows-troubleshooting)
5. [High-Level Context & Intelligence](#5-high-level-context--intelligence)
   - [Live Temporal Anchors & Real-Time Telemetry](#live-temporal-anchors--real-time-telemetry)
   - [Always-On Voice Interaction & Wake Word ("Jarvis")](#always-on-voice-interaction--wake-word-jarvis)
   - [Strict Literal Obedience Protocol](#strict-literal-obedience-protocol)
   - [Natural Speech Synthesis (Edge-TTS)](#natural-speech-synthesis-edge-tts)
   - [Silent Error Logging ("Do Not Speak Errors")](#silent-error-logging-do-not-speak-errors)
6. [Universal Pluggable LLM Configuration](#6-universal-pluggable-llm-configuration)
   - [Supported AI Providers](#supported-ai-providers)
   - [In-App Settings GUI (⚙️ Modal)](#in-app-settings-gui-️-modal)
   - [Local Fallback Autonomous Rule-Based Planner](#local-fallback-autonomous-rule-based-planner)
7. [Autonomous OS Actions Pipeline](#7-autonomous-os-actions-pipeline)
8. [Security Guardrails & Fail-Safes](#8-security-guardrails--fail-safes)
9. [Automated Verification & Pytest Test Suite](#9-automated-verification--pytest-test-suite)

---

## 1. Overview & Vision

**J.A.R.V.I.S.** (*Just A Rather Very Intelligent System*) is an autonomous desktop voice agent inspired by Marvel's Iron Man. Beyond a conversational assistant, J.A.R.V.I.S. is an agentic operating system orchestrator equipped to:
- Perform human-like typing with randomized cadence (jitter: 20ms – 60ms).
- Dynamically navigate, search, and launch applications and project workspaces.
- Autonomously manage directories, read/write files, and execute safeguarded shell commands.
- Continuously listen via an always-on microphone filter activated by the wake-word *"Jarvis"*.
- Render a 60 FPS futuristic sci-fi HUD (*Heads-Up Display*) featuring a dynamic Arc Reactor, audio visualizer, circular radar, and live telemetry.

---

## 2. System Architecture

The system employs a decoupled, client-server architecture communicating locally via WebSocket:

```
┌──────────────────────────────────────────────────────────────┐
│                    PRESENTATIONAL LAYER (HUD)                │
│  Java 21 LTS + OpenJFX 21 + Iron Man Sci-Fi CSS Styling      │
│  - 60 FPS Rotating Arc Reactor Canvas Animation              │
│  - Real-Time Audio Waveform Visualizer & Circular Radar      │
│  - System Telemetry Widgets (CPU, RAM, Disk, WebSocket State)│
│  - Live Activity Terminal & Red Kill-Switch (ABORT TASK)     │
│  - Dynamic LLM Configuration Modal (⚙️ Settings)             │
└──────────────────────────────▲───────────────────────────────┘
                               │ (Bi-directional WebSocket: Port 8765)
┌──────────────────────────────▼───────────────────────────────┐
│                 ORCHESTRATION GATEWAY & BACKEND              │
│  Python 3.12 (FastAPI + Asyncio)                             │
│  - Always-On Wake Word Filter ("Jarvis" Voice Detection)     │
│  - High-Fidelity Edge-TTS Engine (Indonesian & English)      │
│  - High-Level Live Context Injector (Telemetry & Time)       │
│  - Multi-LLM Universal Adapter & Intent Parser               │
│  - Autonomous Local Fallback Rule-Based Planner              │
└──────────────────────────────▲───────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
┌───────────────────────────────┐ ┌─────────────────────────────┐
│       AGENTIC OS CONTROL      │ │      ACID LOCAL MEMORY      │
│ - PyAutoGUI / Pynput          │ │ SQLite 3 (PRAGMA WAL Mode)  │
│ - OpenCV (Webcam Snapshots)   │ │ - Session Message Ledger    │
│ - Subprocess Command Executor │ │ - Task State & Action Audits│
│ - PII & OS Security Guardrails│ │ - Auto Crash Rehydration    │
└───────────────────────────────┘ └─────────────────────────────┘
```

---

## 3. Linux Setup & Installation Guide

### Linux Prerequisites
- **Distribution**: Ubuntu 22.04+, Debian 12+, Fedora 38+, Arch Linux, etc.
- **Java**: OpenJDK 21 LTS (`sudo apt install openjdk-21-jdk`).
- **Build Tool**: Apache Maven 3.8+ (`sudo apt install maven`).
- **Python**: Python 3.12+ with `python3-venv` and `python3-pip`.
- **Media & Audio Packages**: ALSA, PulseAudio/PipeWire, PortAudio (`portaudio19-dev`), eSpeak (`espeak`).
- **Display Server**: X11 (recommended) or Wayland with XWayland compatibility layer.

### Automated Build & Install (Recommended)
From the project root directory, run:
```bash
./jarvis.sh build
```
This automated script will:
1. Initialize the Python virtual environment (`backend-python/.venv`) and install dependencies from `requirements.txt`.
2. Compile and package the JavaFX HUD into an executable fat jar (`dist/jarvis-hud.jar`).
3. Symlink the global command `jarvis` to `/usr/local/bin/jarvis` and `~/.local/bin/jarvis`.
4. Run the full pytest verification suite (13 test cases).

### Global `jarvis` CLI Command
Once built, you can control J.A.R.V.I.S. from any terminal window:
```bash
jarvis
```
CLI arguments:
- `jarvis run` : Launches both the backend orchestrator and the JavaFX HUD simultaneously.
- `jarvis build` : Recompiles and re-installs all project components.
- `jarvis backend` : Starts only the Python backend daemon (port 8765).
- `jarvis gui` : Launches only the JavaFX HUD interface.
- `jarvis test` : Executes the test suite with pytest.
- `jarvis stop` : Terminates any running J.A.R.V.I.S. processes cleanly.

### Manual Step-by-Step Execution

#### 1. Running the Python Backend:
```bash
cd backend-python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python main.py
```
*Backend initializes at `http://127.0.0.1:8765` and serves WebSocket at `ws://127.0.0.1:8765/ws/agent`.*

#### 2. Running the JavaFX HUD:
```bash
cd frontend-javafx
mvn clean javafx:run
```

### Linux Troubleshooting
- **PyAutoGUI / X11 display error**:
  Ensure your display variable is set: `export DISPLAY=:0`. If using pure Wayland, verify XWayland is active or log into an Xorg session.
- **Microphone Permission / ALSA Error**:
  Add your user to the audio group: `sudo usermod -aG audio $USER`.
- **Port 8765 Already in Use**:
  Execute `./jarvis.sh stop` or kill the hanging process with: `fuser -k 8765/tcp`.

---

## 4. Windows (x64) Setup & Installation Guide

### Windows Prerequisites
- **Operating System**: Windows 10 (64-bit) or Windows 11 (64-bit).
- **Java**: Java 21 LTS 64-bit (Oracle JDK 21 or Eclipse Temurin 21).
- **Python**: Python 3.12+ (Ensure *"Add Python to PATH"* is checked during installation).
- **Visual C++ Redistributable**: Required for OpenCV and native audio libraries.

### Fast Setup via Pre-Packaged ZIP (`jarvis-windows-x64.zip`)

For users who want to run J.A.R.V.I.S. immediately without compiling from source:

🔗 **Direct Download Link**: **[Download jarvis-windows-x64.zip (Direct Download)](https://github.com/FIKY0911/Project-A/raw/main/jarvis-windows-x64.zip)**

#### Setup & Execution Steps:
1. **Download ZIP Archive**:
   Download [jarvis-windows-x64.zip](https://github.com/FIKY0911/Project-A/raw/main/jarvis-windows-x64.zip) to your computer.
2. **Extract Archive**:
   Right-click `jarvis-windows-x64.zip`, select **Extract All...**, and specify your desired destination directory (e.g., `C:\JARVIS` or `D:\JARVIS`).
3. **Install Dependencies via `install.exe` (One-time only)**:
   Open the extracted `jarvis-windows-x64` directory and double-click the native installer:
   ```cmd
   install.exe
   ```
   *This native installer executable automatically configures an isolated Python virtual environment and installs all required dependencies. (Note: Running `jarvis.exe` directly will also automatically detect and trigger environment configuration if not yet initialized).*
4. **Launch Application (.exe)**:
   - Double-click **`jarvis.exe`** to launch J.A.R.V.I.S. (automatically starts the Python backend daemon in background and presents the Sci-Fi Iron Man HUD).
   - Run **`jarvis-config.exe`** to configure LLM Provider, API Keys, and Base URLs via a native GUI dialog.

### Manual Windows Installation
If cloning from source:
```cmd
cd backend-python
python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt
python main.py
```
Open a separate Command Prompt:
```cmd
cd frontend-javafx
mvn clean javafx:run
```

### Windows Troubleshooting
- **Windows Defender / SmartScreen Warning**:
  Because `JARVIS.exe` is a custom-compiled binary, click *"More info"* and select *"Run anyway"*.
- **PyAudio Compilation Failure**:
  Install pre-compiled wheels via pip: `pip install pipwin && pipwin install pyaudio`.
- **Microphone Access**:
  Navigate to *Windows Settings* -> *Privacy & Security* -> *Microphone* and ensure *"Let desktop apps access your microphone"* is enabled.

---

## 5. High-Level Context & Intelligence

J.A.R.V.I.S. includes an advanced context injection engine that dynamically computes real-time operational state on every interaction.

### Live Temporal Anchors & Real-Time Telemetry
Every prompt submitted to the AI is enriched with live host context:
- **Exact Date & Time**: Live day of the week, calendar date, and timestamp (`Saturday, 19 September 2026, HH:MM:SS`). Prevents temporal hallucinations.
- **Hardware Telemetry**: Real-time CPU utilization (%), RAM memory consumption (MB & %), and free disk storage.
- **Host Environment**: Operating system kernel, active user (`fiky`), home path, and active working directory.

### Always-On Voice Interaction & Wake Word ("Jarvis")
- **Always-On Listener**: No need to manually toggle microphone buttons on the UI.
- **Wake Word Filter**: Ignores ambient noise and background speech unless the wake word *"Jarvis"* is spoken.
- **Interactive Conversational Flow**:
  - Calling *"Jarvis"* prompts an immediate courteous acknowledgment:
    > *"Yes Sir, ada yang bisa saya bantu?"* (or *"Yes, Sir. How may I assist you?"*)
  - The HUD status switches to `AWAITING_COMMAND` with an active listening visualizer.
  - The user can then issue follow-up commands naturally.

### Strict Literal Obedience Protocol
J.A.R.V.I.S. strictly follows user instructions without unwarranted extrapolations:
- When instructed *"Buka browser"* or *"Open Chrome"*, J.A.R.V.I.S. **only** opens the application.
- When instructed with a compound task (*"Buka chrome lalu cari berita teknologi terkini"*), J.A.R.V.I.S. chains both actions sequentially: launching the application and then querying Google.

### Natural Speech Synthesis (Edge-TTS)
- Speech is synthesized using high-fidelity Edge-TTS neural models (`id-ID-ArdiNeural` for Indonesian, `en-US-ChristopherNeural` for English).
- System prompts forbid the AI from verbalizing raw markdown characters, tables, or JSON code, ensuring natural, human-like voice delivery.

### Silent Error Logging ("Do Not Speak Errors")
- When external LLM APIs experience connection issues, rate limits, or quota errors, the error is displayed visually in the **Recent Activity** HUD panel.
- **Errors are never spoken aloud**, preserving user comfort and avoiding disturbing ambient audio.

---

## 6. Universal Pluggable LLM Configuration

### Supported AI Providers
1. **OpenAI / OpenAI-Compatible Local**:
   - Endpoints: `http://localhost:20128/v1`, `http://localhost:11434/v1`, `https://api.openai.com/v1`, `https://openrouter.ai/api/v1`.
   - Models: `FreeTrial`, `gpt-4o`, `deepseek-chat`, `llama-3`, etc.
2. **Anthropic Claude**:
   - Endpoint: `https://api.anthropic.com`
   - Models: `claude-3-5-sonnet-20241022`, `claude-3-haiku-20240307`.
3. **Google Gemini**:
   - Models: `gemini-1.5-flash`, `gemini-1.5-pro`.
4. **Ollama Local**:
   - Endpoint: `http://localhost:11434`
   - Models: `llama3`, `mistral`, `qwen2.5-coder`.

### In-App Settings GUI (⚙️ Modal)
1. Click the **Settings (⚙️)** gear icon in the upper-right corner of the HUD.
2. Select your desired LLM Provider from the dropdown menu.
3. Enter your **Model Name**, **API Key** (if required), and **Base URL**.
4. Click **Save Configuration**. The changes apply immediately without restarting.

### Local Fallback Autonomous Rule-Based Planner
If the LLM endpoint is unreachable, J.A.R.V.I.S. switches to its internal local planner, enabling:
- Answering current time and date queries.
- Answering system hardware diagnostics questions.
- Dynamically launching installed applications and project folders.
- Creating directories and executing web searches.

---

## 7. Autonomous OS Actions Pipeline

J.A.R.V.I.S. generates structured JSON execution plans processed asynchronously by `OSController`:

| Action Type | Example User Command | JSON Format | Description |
| :--- | :--- | :--- | :--- |
| `OPEN_APP` | *"Open VSCode in JARVIS folder"* | `{"action": "OPEN_APP", "app": "code", "path": "JARVIS"}` | Launches application at resolved folder path. |
| `CREATE_DIR`| *"Create folder projects_test"* | `{"action": "CREATE_DIR", "path": "projects_test"}` | Safely creates directory at target location. |
| `WRITE_FILE`| *"Write notes to todo.txt"* | `{"action": "WRITE_FILE", "path": "todo.txt", "content": "..."}` | Writes content to file. |
| `READ_FILE` | *"Read config.json"* | `{"action": "READ_FILE", "path": "config.json"}` | Reads local file contents for analysis. |
| `SEARCH_WEB`| *"Search for AI news"* | `{"action": "SEARCH_WEB", "query": "AI news"}` | Opens browser to Google Search. |
| `OPEN_URL` | *"Open github.com"* | `{"action": "OPEN_URL", "url": "https://github.com"}` | Opens specific URL in default browser. |
| `TYPE` | *"Type Hello World"* | `{"action": "TYPE", "text": "Hello World"}` | Natural typing with 20–60ms jitter. |
| `HOTKEY` | *"Press ctrl c"* | `{"action": "HOTKEY", "keys": ["ctrl", "c"]}` | Sends keyboard shortcuts. |
| `SYSTEM_CONTROL`| *"Volume up"* | `{"action": "SYSTEM_CONTROL", "control": "up"}` | Adjusts system volume (up, down, mute). |
| `SCREENSHOT`| *"Take a screenshot"* | `{"action": "SCREENSHOT"}` | Saves desktop screenshot to snapshots dir. |
| `CAMERA_SNAPSHOT`| *"Capture webcam image"* | `{"action": "CAMERA_SNAPSHOT"}` | Captures single camera frame using OpenCV. |

---

## 8. Security Guardrails & Fail-Safes

1. **SEC-01: PII & Credentials Guardrail**:
   - Pre-screens instructions against regex patterns for credit cards, phone numbers, emails, and passwords before automation executes.
2. **SEC-02: OS Command Protection Guardrail**:
   - Rejects dangerous commands (`rm -rf`, `format`, `dd`) and protects critical system paths (`/etc`, `/boot`, `C:\Windows\System32`).
3. **SEC-04: Instant UI Kill-Switch**:
   - Dedicated red **ABORT TASK** button on the HUD to immediately interrupt active background task workers.
4. **SEC-05: Hardware Fail-Safe**:
   - Built-in `pyautogui.FAILSAFE = True`. Slamming the mouse cursor into any screen corner aborts cursor actions instantly.

---

## 9. Automated Verification & Pytest Test Suite

Run the full automated test suite containing 13 comprehensive test cases:

```bash
cd backend-python
./.venv/bin/pytest tests/test_jarvis_core.py -v
```

Verification suite:
1. `test_srd_tc_04_pii_guardrail_detection`: PII regex filter verification.
2. `test_srd_tc_os_command_protection`: System command blacklisting verification.
3. `test_srd_tc_05_database_wal_and_rehydration`: SQLite WAL and session rehydration.
4. `test_srd_tc_02_pluggable_llm_switch`: Dynamic LLM configuration swap.
5. `test_srd_tc_03_humanlike_typing_jitter`: Natural typing jitter interval (20ms – 60ms).
6. `test_srd_tc_01_proactive_greeting`: Proactive initialization greeting.
7. `test_os_actions_and_local_planner`: OS action dispatch and execution.
8. `test_wake_word_filtering`: Wake-word gating ("Jarvis").
9. `test_dynamic_app_and_path_resolution`: Fuzzy path and application resolution.
10. `test_silent_error_and_vocal_success`: Visual error logging without vocal disturbance.
11. `test_dynamic_literal_obedience_and_no_unwanted_search`: Strict obedience to user intent.
12. `test_conversational_greeting_and_followup_flow`: Greeting flow and follow-up window.
13. `test_high_level_context_and_intelligence`: Real-time telemetry and temporal context injection.
