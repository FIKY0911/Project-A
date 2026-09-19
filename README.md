# J.A.R.V.I.S. (Just A Rather Very Intelligent System)
### Autonomous OS Desktop Voice Agent & Iron Man Sci-Fi HUD

[![Platform: Linux & Windows](https://img.shields.io/badge/Platform-Linux%20%7C%20Windows%20x64-00f0ff.svg)](#)
[![Python: 3.12+](https://img.shields.io/badge/Python-3.12%2B-3776ab.svg)](#)
[![Java: OpenJDK 21 LTS](https://img.shields.io/badge/Java-21%20LTS-f89820.svg)](#)
[![Tests: 13/13 Passed](https://img.shields.io/badge/Pytest-13%2F13%20Passed-brightgreen.svg)](#)
[![Docs: ID & EN](https://img.shields.io/badge/Documentation-Bilingual%20(ID%20%2F%20EN)-blueviolet.svg)](#)
[![Download: Windows ZIP](https://img.shields.io/badge/Download-Windows%20x64%20ZIP-success?logo=windows&logoColor=white)](https://github.com/FIKY0911/Project-A/raw/main/jarvis-windows-x64.zip)

---

### 🌐 Quick Documentation Links & Downloads
- 📥 **[Download J.A.R.V.I.S. Windows x64 ZIP (Ready to Run)](https://github.com/FIKY0911/Project-A/raw/main/jarvis-windows-x64.zip)**
- 🇮🇩 **[Panduan Lengkap Bahasa Indonesia (docs/MANUAL_ID.md)](docs/MANUAL_ID.md)**
- 🇬🇧 **[Full English Technical Manual (docs/MANUAL_EN.md)](docs/MANUAL_EN.md)**

---

## 🇮🇩 Ringkasan Proyek (Bahasa Indonesia)

**J.A.R.V.I.S.** adalah asisten desktop otonom cerdas berbasis suara (*voice agent*) dengan antarmuka grafis futuristik bertema Iron Man HUD (*Heads-Up Display*) 60 FPS menggunakan JavaFX 21, didukung backend asinkron Python 3.12 (FastAPI), serta basis data lokal tahan-crash SQLite 3 WAL.

### Fitur Unggulan:
1. **Mikrofon Selalu Aktif & Filter Kata Panggil ("Jarvis")**: Mendengarkan secara berkelanjutan tanpa perlu klik tombol mic. Hanya bereaksi jika dipanggil *"Jarvis"*, dan menyapa ramah: *"Yes Sir, ada yang bisa saya bantu?"*.
2. **Kepatuhan Literal Dinamis (Literal Obedience)**: JARVIS hanya mengeksekusi apa yang Anda minta (misal: *"buka browser"* hanya membuka browser tanpa pencarian liar).
3. **High-Level Context & Live Telemetry**: Mengetahui waktu & tanggal nyata presisi, utilisasi CPU, konsumsi RAM, sisa disk, serta status sistem secara real-time.
4. **Universal Pluggable LLM**: Mendukung OpenAI, Local OpenAI-compatible (`http://localhost:20128/v1`, vLLM, LM Studio), Anthropic Claude, Google Gemini, Ollama, serta **Local Fallback Planner** bawaan jika internet/API offline.
5. **Penanganan Eror Senyap (Silent Error)**: Pesan eror API ditampilkan di Recent Activity tanpa dibaca bersuara keras (*"jangan dibaca"*).
6. **Otomasi OS Lengkap**: Pengetikan natural (jitter 20–60ms), membuka aplikasi di folder spesifik, membuat folder (`CREATE_DIR`), membaca/menulis file, kontrol audio, screenshot, dan foto webcam.

---

## 🇬🇧 Project Overview (English)

**J.A.R.V.I.S.** is an autonomous desktop voice agent featuring a 60 FPS futuristic Iron Man HUD (*Heads-Up Display*) crafted in JavaFX 21, powered by a Python 3.12 (FastAPI) asynchronous orchestration backend, and local crash-resilient SQLite 3 WAL memory.

### Core Capabilities:
1. **Always-On Listening with Wake Word ("Jarvis")**: Continuous audio stream filtering ambient noise, triggering on *"Jarvis"* with an articulate response: *"Yes Sir, ada yang bisa saya bantu?"*.
2. **Strict Literal Obedience**: JARVIS executes strictly what is commanded (e.g., *"open browser"* only opens the browser without unwanted web searches).
3. **High-Level Context & Live Telemetry**: Live temporal anchors (real-time date/time), live CPU/RAM/Disk metrics via `psutil`, and host environmental awareness.
4. **Universal Pluggable LLM Engine**: Native support for OpenAI, local OpenAI-compatible endpoints (`http://localhost:20128/v1`, vLLM, LM Studio), Anthropic Claude, Google Gemini, Ollama, and an autonomous **Local Fallback Planner**.
5. **Silent Error Display**: Connection errors are visually displayed in Recent Activity without disturbing spoken audio.
6. **Comprehensive OS Control**: Human-like typing cadence (20–60ms jitter), folder-aware app launching, autonomous directory creation (`CREATE_DIR`), file I/O, system volume control, screenshots, and OpenCV webcam capture.

---

## 🏛️ System Architecture / Arsitektur Sistem

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

## 🚀 Quick Start / Panduan Cepat

### 🐧 Linux

#### 1. Build & Install (Otomatis / Sekali Saja):
```bash
./jarvis.sh build
```

#### 2. Jalankan J.A.R.V.I.S. (Global Command):
Dari direktori mana pun di terminal:
```bash
jarvis
```
*Atau jalankan `./jarvis.sh run` di dalam folder project.*

---

### 🪟 Windows (x64)

#### 1. Download & Ekstrak Paket Siap Pakai:
- **Tautan Unduh ZIP**: 📦 **[Unduh jarvis-windows-x64.zip](https://github.com/FIKY0911/Project-A/raw/main/jarvis-windows-x64.zip)**
- Setelah file selesai diunduh, klik kanan pada file **`jarvis-windows-x64.zip`**, pilih **Extract All...** (Ekstrak Semua) ke folder pilihan Anda (contoh: `C:\JARVIS` atau `D:\JARVIS`).

#### 2. Instalasi Dependensi via Native Executable (Hanya Sekali di Awal):
Buka folder hasil ekstraksi (`jarvis-windows-x64`), lalu klik ganda file installer:
```cmd
install.exe
```
*(Program installer native ini akan otomatis menyiapkan virtual environment Python dan mengunduh seluruh dependensi yang diperlukan. Anda juga bisa langsung menjalankan `jarvis.exe`, program akan otomatis mendeteksi dan menyiapkan dependensi jika belum terinstal).*

#### 3. Jalankan Aplikasi Langsung (.exe):
Di dalam folder hasil ekstraksi:
- **Klik ganda `jarvis.exe`** untuk meluncurkan JARVIS secara langsung (backend Python dan HUD JavaFX akan aktif otomatis di latar belakang).
- **Klik ganda `jarvis-config.exe`** jika ingin mengatur API Key dan model LLM melalui dialog grafis Windows sebelum atau sesudah memulai.

---

## ⚙️ In-App LLM Settings / Pengaturan AI

Anda dapat mengganti model AI secara langsung dari HUD tanpa perlu me-restart aplikasi:
1. Klik ikon roda gigi **Settings (⚙️)** di pojok kanan atas HUD.
2. Pilih provider (misal: *OpenAI Compatible Local*).
3. Masukkan Endpoint (contoh: `http://localhost:20128/v1`), Model Name (`FreeTrial`), dan API Key (jika diperlukan).
4. Klik **Save Configuration**.

---

## 🧪 Automated Testing / Hasil Verifikasi

Seluruh 13 skenario uji penerimaan lulus 100%:
```bash
backend-python/tests/test_jarvis_core.py::test_srd_tc_04_pii_guardrail_detection PASSED
backend-python/tests/test_jarvis_core.py::test_srd_tc_os_command_protection PASSED
backend-python/tests/test_jarvis_core.py::test_srd_tc_05_database_wal_and_rehydration PASSED
backend-python/tests/test_jarvis_core.py::test_srd_tc_02_pluggable_llm_switch PASSED
backend-python/tests/test_jarvis_core.py::test_srd_tc_03_humanlike_typing_jitter PASSED
backend-python/tests/test_jarvis_core.py::test_srd_tc_01_proactive_greeting PASSED
backend-python/tests/test_jarvis_core.py::test_os_actions_and_local_planner PASSED
backend-python/tests/test_jarvis_core.py::test_wake_word_filtering PASSED
backend-python/tests/test_jarvis_core.py::test_dynamic_app_and_path_resolution PASSED
backend-python/tests/test_jarvis_core.py::test_silent_error_and_vocal_success PASSED
backend-python/tests/test_jarvis_core.py::test_dynamic_literal_obedience_and_no_unwanted_search PASSED
backend-python/tests/test_jarvis_core.py::test_conversational_greeting_and_followup_flow PASSED
backend-python/tests/test_jarvis_core.py::test_high_level_context_and_intelligence PASSED
======================== 13 passed, 2 warnings in 0.59s ========================
```

---

## 📚 Detailed Documentation / Dokumentasi Terperinci

Untuk pembahasan teknis mendalam mengenai guardrails, resolusi path dinamis, skema database SQLite, dan troubleshooting lengkap per OS:
- **[Manual Bahasa Indonesia](docs/MANUAL_ID.md)**
- **[English Manual](docs/MANUAL_EN.md)**
