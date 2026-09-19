# J.A.R.V.I.S. (Just A Rather Very Intelligent System)
## Panduan Dokumentasi Lengkap & Manual Operasional (Bahasa Indonesia)

---

### Daftar Isi
1. [Tentang J.A.R.V.I.S. & Visi Sistem](#1-tentang-jarvis--visi-sistem)
2. [Arsitektur Teknis Sistem](#2-arsitektur-teknis-sistem)
3. [Panduan Instalasi & Menjalankan di Linux](#3-panduan-instalasi--menjalankan-di-linux)
   - [Persyaratan Sistem Linux](#persyaratan-sistem-linux)
   - [Instalasi Otomatis (Direkomendasikan)](#instalasi-otomatis-direkomendasikan)
   - [Perintah Global `jarvis`](#perintah-global-jarvis)
   - [Instalasi & Menjalankan Manual (Step-by-Step)](#instalasi--menjalankan-manual-step-by-step)
   - [Troubleshooting & Solusi Linux](#troubleshooting--solusi-linux)
4. [Panduan Instalasi & Menjalankan di Windows (x64)](#4-panduan-instalasi--menjalankan-di-windows-x64)
   - [Persyaratan Sistem Windows](#persyaratan-sistem-windows)
   - [Instalasi Cepat via Paket ZIP (`jarvis-windows-x64.zip`)](#instalasi-cepat-via-paket-zip-jarvis-windows-x64zip)
   - [Eksekusi via Native Windows Launcher (`JARVIS.exe`)](#eksekusi-via-native-windows-launcher-jarvisexe)
   - [Instalasi Manual di Windows](#instalasi-manual-di-windows)
   - [Troubleshooting & Solusi Windows](#troubleshooting--solusi-windows)
5. [Kecerdasan Buatan & High-Level Live Context](#5-kecerdasan-buatan--high-level-live-context)
   - [Telemetri Sistem & Waktu Nyata (Temporal Anchors)](#telemetri-sistem--waktu-nyata-temporal-anchors)
   - [Interaksi Suara & Wake Word ("Jarvis")](#interaksi-suara--wake-word-jarvis)
   - [Kepatuhan Literal Mutlak (Literal Obedience)](#kepatuhan-literal-mutlak-literal-obedience)
   - [Protokol Suara Alami (Natural Spoken Voice)](#protokol-suara-alami-natural-spoken-voice)
   - [Penanganan Eror Senyap (Silent Error Display)](#penanganan-eror-senyap-silent-error-display)
6. [Konfigurasi Model LLM (Universal Pluggable LLM)](#6-konfigurasi-model-llm-universal-pluggable-llm)
   - [Provider yang Didukung](#provider-yang-didukung)
   - [Pengaturan via GUI HUD (Ikon Gear ⚙️)](#pengaturan-via-gui-hud-ikon-gear-️)
   - [Local Fallback Rule-Based Planner](#local-fallback-rule-based-planner)
7. [Daftar Tindakan & Otomasi OS (Actions Pipeline)](#7-daftar-tindakan--otomasi-os-actions-pipeline)
8. [Sistem Keamanan & Guardrails](#8-sistem-keamanan--guardrails)
9. [Pengujian Sistem & Verifikasi Otomatis (Pytest)](#9-pengujian-sistem--verifikasi-otomatis-pytest)

---

## 1. Tentang J.A.R.V.I.S. & Visi Sistem

**J.A.R.V.I.S.** (*Just A Rather Very Intelligent System*) adalah asisten desktop otonom cerdas terinspirasi dari fiksi ilmiah Marvel Iron Man. Berbeda dari bot percakapan biasa, J.A.R.V.I.S. memiliki kontrol langsung atas sistem operasi Anda untuk:
- Mengeksekusi pengetikan natural manusiawi (*human-like typing*).
- Menavigasi dan meluncurkan aplikasi dengan pencarian folder dinamis.
- Mengelola berkas, membuat folder, dan menjalankan perintah shell yang aman.
- Mendengarkan perintah suara Anda secara interaktif melalui mikrofon selalu aktif (*always-on listening* dengan wake-word "Jarvis").
- Menampilkan visualisasi antarmuka HUD (*Heads-Up Display*) 60 FPS bertema Arc Reactor dan radar telemetri sistem.

---

## 2. Arsitektur Teknis Sistem

Sistem dirancang dengan arsitektur terpisah (*decoupled client-server*) yang tangguh:

```
┌──────────────────────────────────────────────────────────────┐
│                    LAPISAN PRESENTASI (HUD)                  │
│  Java 21 LTS + OpenJFX 21 + CSS Tema Iron Man Sci-Fi         │
│  - Animasi Arc Reactor Berputar 60 FPS                       │
│  - Real-Time Audio Visualizer & Radar Sweep                  │
│  - Telemetri Sistem (CPU, RAM, Disk, Status WebSocket)       │
│  - Terminal Aktivitas Terbaru & Tombol Kill-Switch (ABORT)   │
│  - Modal Konfigurasi LLM Terintegrasi (⚙️ Settings)          │
└──────────────────────────────▲───────────────────────────────┘
                               │ (Bi-directional WebSocket: Port 8765)
┌──────────────────────────────▼───────────────────────────────┐
│                 ORCHESTRATION GATEWAY & BACKEND              │
│  Python 3.12 (FastAPI + Asyncio)                             │
│  - Always-On Wake Word Engine ("Jarvis" Voice Filter)        │
│  - Edge-TTS Voice Synthesizer (Indonesia: id-ID-ArdiNeural)  │
│  - High-Level Context Injector (Waktu & Telemetri Nyata)     │
│  - Multi-LLM Universal Adapter & Intent Parser               │
│  - Local Fallback Autonomous Rule Planner                    │
└──────────────────────────────▲───────────────────────────────┘
                               │
               ┌───────────────┴───────────────┐
               ▼                               ▼
┌───────────────────────────────┐ ┌─────────────────────────────┐
│       KONTROL OTOMASI OS      │ │      MEMORI LOKAL ACID      │
│ - PyAutoGUI / Pynput          │ │ SQLite 3 (PRAGMA WAL Mode)  │
│ - OpenCV (Kamera Webcam)      │ │ - Log Percakapan Sesi       │
│ - Subprocess Command Executor │ │ - Riwayat Status Task & Aksi│
│ - PII & Security Guardrails   │ │ - Rehidrasi Otomatis Crash  │
└───────────────────────────────┘ └─────────────────────────────┘
```

---

## 3. Panduan Instalasi & Menjalankan di Linux

### Persyaratan Sistem Linux
- **Distro**: Ubuntu 22.04+, Debian 12+, Fedora 38+, Arch Linux, dsb.
- **Java**: OpenJDK 21 LTS (`sudo apt install openjdk-21-jdk`).
- **Build Tool**: Apache Maven 3.8+ (`sudo apt install maven`).
- **Python**: Python 3.12+ beserta `python3-venv` dan `python3-pip`.
- **Dependensi Media/Audio**: ALSA, PulseAudio/PipeWire, PortAudio (`portaudio19-dev`), eSpeak (`espeak`).
- **Dependensi Tampilan**: X11 (disarankan) atau Wayland dengan layer XWayland.

### Instalasi Otomatis (Direkomendasikan)
Di root folder JARVIS, jalankan skrip build:
```bash
./jarvis.sh build
```
Skrip ini akan secara otomatis:
1. Menyiapkan virtual environment Python (`backend-python/.venv`) dan menginstal seluruh dependencies (`requirements.txt`).
2. Mengompilasi dan membungkus frontend JavaFX menjadi *fat executable jar* (`jarvis-hud.jar`).
3. Mendaftarkan perintah global `jarvis` ke sistem (`/usr/local/bin/jarvis` dan `~/.local/bin/jarvis`).
4. Menjalankan verifikasi unit testing lengkap (13 test cases).

### Perintah Global `jarvis`
Setelah build selesai, Anda dapat menjalankan J.A.R.V.I.S. langsung dari terminal mana pun:
```bash
jarvis
```
Atau menggunakan argumen:
- `jarvis run` : Menjalankan backend dan GUI HUD bersamaan.
- `jarvis build` : Mengompilasi ulang seluruh komponen proyek.
- `jarvis backend` : Menjalankan backend Python saja (port 8765).
- `jarvis gui` : Menjalankan antarmuka grafis JavaFX saja.
- `jarvis test` : Menjalankan unit tests dengan pytest.
- `jarvis stop` : Menghentikan seluruh proses J.A.R.V.I.S. yang sedang aktif.

### Instalasi & Menjalankan Manual (Step-by-Step)

#### 1. Menjalankan Backend Python:
```bash
cd backend-python
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
python main.py
```
*Backend akan online di `http://127.0.0.1:8765` dan membuka WebSocket di `ws://127.0.0.1:8765/ws/agent`.*

#### 2. Menjalankan Frontend JavaFX HUD:
```bash
cd frontend-javafx
mvn clean javafx:run
```

### Troubleshooting & Solusi Linux
- **Eror PyAutoGUI / X11 display**:
  Pastikan variabel display terdefinisi: `export DISPLAY=:0`. Jika menggunakan Wayland murni tanpa XWayland, jalankan dengan environment compatibility atau ganti sesi ke Ubuntu on Xorg.
- **Eror Perizinan Mikrofon**:
  Pastikan user Anda tergabung dalam grup audio: `sudo usermod -aG audio $USER`.
- **Eror Port 8765 Telah Digunakan**:
  Jalankan `./jarvis.sh stop` atau bunuh proses lama dengan: `fuser -k 8765/tcp`.

---

## 4. Panduan Instalasi & Menjalankan di Windows (x64)

### Persyaratan Sistem Windows
- **OS**: Windows 10 (64-bit) atau Windows 11 (64-bit).
- **Java**: Java 21 LTS 64-bit (Oracle JDK 21 atau Eclipse Temurin 21).
- **Python**: Python 3.12+ (Pastikan opsi *"Add Python to PATH"* dicentang saat instalasi).
- **Visual C++ Redistributable**: Diperlukan untuk modul OpenCV dan PyAudio di Windows.

### Instalasi Cepat via Paket ZIP Siap Pakai (`jarvis-windows-x64.zip`)

Bagi pengguna yang ingin langsung menggunakan J.A.R.V.I.S. tanpa perlu mengompilasi kode sumber:

🔗 **Link Download Paket ZIP**: **[Unduh jarvis-windows-x64.zip (Direct Download)](https://github.com/FIKY0911/Project-A/raw/main/jarvis-windows-x64.zip)**

#### Langkah-Langkah Pemasangan & Menjalankan:
1. **Unduh Arsip ZIP**:
   Unduh file [jarvis-windows-x64.zip](https://github.com/FIKY0911/Project-A/raw/main/jarvis-windows-x64.zip) ke komputer Anda.
2. **Ekstrak File ZIP**:
   Klik kanan file `jarvis-windows-x64.zip`, pilih **Extract All...** (Ekstrak Semua), lalu arahkan ke lokasi folder yang diinginkan (misalnya `C:\JARVIS` atau `D:\JARVIS`).
3. **Instal Dependensi via `install.exe` (Hanya Sekali di Awal)**:
   Masuk ke folder hasil ekstraksi `jarvis-windows-x64`, lalu klik ganda file installer native:
   ```cmd
   install.exe
   ```
   *Program installer `.exe` ini akan secara otomatis menyiapkan virtual environment Python dan mengunduh seluruh dependensi yang diperlukan. (Catatan: Jika Anda langsung menjalankan `jarvis.exe`, launcher juga akan otomatis mendeteksi dan menjalankan setup lingkungan secara mandiri).*
4. **Jalankan Aplikasi (.exe)**:
   - Klik ganda **`jarvis.exe`** untuk langsung menjalankan sistem. Launcher ini akan mengaktifkan backend Python di latar belakang secara otomatis dan membuka antarmuka HUD Iron Man.
   - Gunakan **`jarvis-config.exe`** jika Anda ingin menyesuaikan endpoint API LLM, API Key, dan nama model AI via GUI.

### Instalasi Manual di Windows
Jika Anda melakukan clone langsung dari repositori git:
```cmd
cd backend-python
python -m venv .venv
call .venv\Scripts\activate.bat
pip install -r requirements.txt
python main.py
```
Buka jendela Command Prompt baru:
```cmd
cd frontend-javafx
mvn clean javafx:run
```

### Troubleshooting & Solusi Windows
- **Peringatan Windows Defender / SmartScreen**:
  Karena `JARVIS.exe` dikompilasi secara mandiri (*self-built binary*), klik *"More info"* lalu pilih *"Run anyway"*.
- **Eror PyAudio pada Windows**:
  Jika instalasi PyAudio via pip gagal, instal pip wheel resmi dari PyPI atau jalankan: `pip install pipwin && pipwin install pyaudio`.
- **Pengaturan Izin Mikrofon**:
  Buka *Windows Settings* -> *Privacy & Security* -> *Microphone*, pastikan *"Let desktop apps access your microphone"* dalam posisi **ON**.

---

## 5. Kecerdasan Buatan & High-Level Live Context

J.A.R.V.I.S. dilengkapi dengan sistem injeksi konteks tingkat tinggi yang diperbarui secara dinamis pada setiap pemanggilan prompt.

### Telemetri Sistem & Waktu Nyata (Temporal Anchors)
Setiap permintaan ke AI disuntikkan data operasional terkini:
- **Waktu & Tanggal Nyata**: Mengirimkan hari, tanggal, bulan, tahun, dan jam/menit/detik presisi dari host. JARVIS tidak akan berhalusinasi perihal waktu.
- **Telemetri Perangkat Keras**: Utilisasi CPU saat ini (%), penggunaan RAM (MB & %), dan sisa kapasitas penyimpanan harddisk.
- **Informasi Host**: Nama pengguna aktif (`fiky`), sistem operasi (`Linux`/`Windows`), direktori kerja proyek.

### Interaksi Suara & Wake Word ("Jarvis")
- **Mikrofon Selalu Aktif (Always-On Listener)**: Anda tidak perlu menekan tombol mic berulang kali di UI.
- **Filter Wake Word Cerdas**: J.A.R.V.I.S. hanya memproses suara jika Anda menyebutkan kata panggil *"Jarvis"*, *"Halo Jarvis"*, *"Hey Jarvis"*, atau sedang dalam jendela percakapan aktif.
- **Alur Sapaan Interaktif**:
  - Jika Anda memanggil: *"Jarvis"*, ia akan langsung menyapa dan mengonfirmasi kesiapan:
    > *"Yes Sir, ada yang bisa saya bantu?"* (atau *"Yes, Sir. How may I assist you?"*)
  - Status UI HUD berubah menjadi `AWAITING_COMMAND` dengan visualizer aktif.
  - Setelah itu, Anda dapat langsung menyebutkan perintah lanjutan Anda.

### Kepatuhan Literal Mutlak (Literal Obedience)
J.A.R.V.I.S. dibangun dengan prinsip kepatuhan dinamis:
- Jika Anda memerintahkan *"Buka browser"* atau *"Open Chrome"*, J.A.R.V.I.S. **hanya** akan membuka aplikasi browser dan tidak akan mencari berita sendiri.
- Jika Anda memerintahkan kombinasi *"Buka chrome lalu cari berita teknologi"*, J.A.R.V.I.S. akan merantai dua aksi: membuka aplikasi, lalu menjalankan pencarian web yang diminta.

### Protokol Suara Alami (Natural Spoken Voice)
- Jawaban suara disintesis melalui Edge-TTS (`id-ID-ArdiNeural` untuk Indonesia, `en-US-ChristopherNeural` untuk Inggris).
- Prompt sistem melarang AI menyertakan format mentah markdown (tabel, simbol pagar `#`, asterisk `**`, JSON mentah) pada teks ucapan agar suara terdengar seperti manusia berbicara.

### Penanganan Eror Senyap (Silent Error Display)
- Jika koneksi API LLM eksternal bermasalah (misal *connection refused* atau kuota habis), teks pesan eror akan dimunculkan secara visual di area **Recent Activity** pada HUD.
- **Eror tidak akan dibacakan dengan suara keras**, menjaga kenyamanan pengguna. Suara hanya digunakan saat sistem berhasil mengeksekusi instruksi.

---

## 6. Konfigurasi Model LLM (Universal Pluggable LLM)

### Provider yang Didukung
1. **OpenAI / OpenAI Compatible Local**:
   - Endpoint: `http://localhost:20128/v1`, `http://localhost:11434/v1`, `https://api.openai.com/v1`, `https://openrouter.ai/api/v1`.
   - Model: `FreeTrial`, `gpt-4o`, `deepseek-chat`, `llama-3`, dsb.
2. **Anthropic Claude**:
   - Endpoint: `https://api.anthropic.com`
   - Model: `claude-3-5-sonnet-20241022`, `claude-3-haiku-20240307`.
3. **Google Gemini**:
   - Model: `gemini-1.5-flash`, `gemini-1.5-pro`.
4. **Ollama Lokal**:
   - Endpoint: `http://localhost:11434`
   - Model: `llama3`, `mistral`, `qwen2.5-coder`.

### Pengaturan via GUI HUD (Ikon Gear ⚙️)
1. Klik tombol gear **Settings (⚙️)** di pojok kanan atas HUD.
2. Pilih LLM Provider dari menu dropdown.
3. Masukkan **Model Name**, **API Key** (jika ada), dan **Base URL** (contoh: `http://localhost:20128/v1`).
4. Klik **Save Configuration**. Konfigurasi langsung aktif seketika tanpa perlu me-restart aplikasi.

### Local Fallback Rule-Based Planner
Jika koneksi internet terputus atau API LLM offline, J.A.R.V.I.S. secara otomatis beralih ke *Autonomous Local Planner* internal. Planner lokal ini dapat:
- Menjawab pertanyaan waktu dan tanggal (*"jam berapa sekarang"*, *"hari apa ini"*).
- Menjawab status kondisi hardware (*"status sistem"*).
- Membuka aplikasi apa pun yang terinstal di komputer.
- Membuka direktori dan workspace proyek.
- Membuat folder baru dan menjalankan pencarian web.

---

## 7. Daftar Tindakan & Otomasi OS (Actions Pipeline)

J.A.R.V.I.S. dapat menghasilkan rencana aksi terstruktur berbasis JSON untuk dieksekusi secara asinkron oleh `OSController`:

| Tipe Aksi | Contoh Perintah | Parameter JSON | Penjelasan |
| :--- | :--- | :--- | :--- |
| `OPEN_APP` | *"Buka VSCode di folder JARVIS"* | `{"action": "OPEN_APP", "app": "code", "path": "JARVIS"}` | Meluncurkan aplikasi di folder target dengan resolusi fuzzy path. |
| `CREATE_DIR` | *"Buat folder project_baru"* | `{"action": "CREATE_DIR", "path": "project_baru"}` | Membuat direktori baru di path aman. |
| `WRITE_FILE` | *"Simpan catatan ke todo.txt"* | `{"action": "WRITE_FILE", "path": "todo.txt", "content": "..."}` | Menulis isi file teks secara otonom. |
| `READ_FILE` | *"Baca isi file config.json"* | `{"action": "READ_FILE", "path": "config.json"}` | Membaca isi file lokal untuk dianalisis. |
| `SEARCH_WEB` | *"Cari artikel tentang AI"* | `{"action": "SEARCH_WEB", "query": "artikel tentang AI"}` | Membuka browser bawaan dan mencari via Google. |
| `OPEN_URL` | *"Buka github.com"* | `{"action": "OPEN_URL", "url": "https://github.com"}` | Membuka tautan URL di web browser. |
| `TYPE` | *"Ketik halo dunia"* | `{"action": "TYPE", "text": "halo dunia"}` | Mengetik teks dengan jitter natural 20–60ms. |
| `HOTKEY` | *"Tekan ctrl c"* | `{"action": "HOTKEY", "keys": ["ctrl", "c"]}` | Mengeksekusi kombinasi tombol keyboard. |
| `SYSTEM_CONTROL`| *"Besarkan volume"* | `{"action": "SYSTEM_CONTROL", "control": "up"}` | Mengatur volume suara sistem (up, down, mute). |
| `SCREENSHOT` | *"Ambil tangkapan layar"* | `{"action": "SCREENSHOT"}` | Mengambil screenshot layar desktop ke folder snapshots. |
| `CAMERA_SNAPSHOT`| *"Ambil foto webcam"* | `{"action": "CAMERA_SNAPSHOT"}` | Menangkap 1 frame kamera melalui OpenCV. |

---

## 8. Sistem Keamanan & Guardrails

1. **SEC-01: PII & Credentials Guardrail**:
   - Memindai setiap teks instruksi terhadap pola regex kartu kredit, nomor telepon, email, dan kata sandi sebelum aksi pengetikan diizinkan.
2. **SEC-02: OS Command Protection Guardrail**:
   - Mencegah eksekusi perintah destruktif seperti `rm -rf`, `format`, `mkfs`, serta memblokir manipulasi direktori sistem sensitif (`/etc`, `/boot`, `/sys`, `C:\Windows\System32`).
3. **SEC-04: Instant UI Kill-Switch**:
   - Tombol **ABORT TASK** berwarna merah pada HUD yang secara instan menghentikan *action loop* yang sedang berlangsung di backend.
4. **SEC-05: Hardware Fail-Safe**:
   - Integrasi `pyautogui.FAILSAFE = True`. Gerakkan kursor ke salah satu dari 4 sudut layar monitor untuk menghentikan automasi mouse secara fisik.

---

## 9. Pengujian Sistem & Verifikasi Otomatis (Pytest)

Seluruh komponen sistem diuji secara berkala dengan 13 unit test terintegrasi:

```bash
cd backend-python
./.venv/bin/pytest tests/test_jarvis_core.py -v
```

Daftar pengujian:
1. `test_srd_tc_04_pii_guardrail_detection`: Deteksi PII dan proteksi kebocoran data.
2. `test_srd_tc_os_command_protection`: Pencegahan eksekusi perintah OS berbahaya.
3. `test_srd_tc_05_database_wal_and_rehydration`: Verifikasi mode SQLite WAL dan rehidrasi riwayat.
4. `test_srd_tc_02_pluggable_llm_switch`: Pertukaran adapter LLM secara dinamis.
5. `test_srd_tc_03_humanlike_typing_jitter`: Interval pengetikan alami (20ms – 60ms).
6. `test_srd_tc_01_proactive_greeting`: Sapaan proaktif saat inisialisasi.
7. `test_os_actions_and_local_planner`: Eksekusi aksi sistem operasi mandiri.
8. `test_wake_word_filtering`: Penyaringan wake-word suara "Jarvis".
9. `test_dynamic_app_and_path_resolution`: Resolusi cerdas nama aplikasi dan folder.
10. `test_silent_error_and_vocal_success`: Penanganan eror senyap di UI tanpa dibaca suara keras.
11. `test_dynamic_literal_obedience_and_no_unwanted_search`: Kepatuhan literal mutlak pada instruksi pengguna.
12. `test_conversational_greeting_and_followup_flow`: Alur percakapan sapaan dan jendela tunggu perintah.
13. `test_high_level_context_and_intelligence`: Konteks operasional tingkat tinggi (telemetri & waktu nyata).
