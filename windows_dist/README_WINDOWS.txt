========================================================================
                      J.A.R.V.I.S. FOR WINDOWS (x64)
                   Iron Man AI Desktop Voice Assistant
           Panduan Penggunaan Windows / Windows Operational Guide
========================================================================

[EN] SYSTEM REQUIREMENTS / [ID] PERSYARATAN SISTEM:
1. Windows 10 / 11 (64-bit)
2. Python 3.10+ (Check "Add Python to PATH" during install / Pastikan dicentang)
3. Java 21 LTS 64-bit (https://adoptium.net / Eclipse Temurin 21)
4. Microphone & Speakers (Ensure microphone permission is ON in Windows Settings)

------------------------------------------------------------------------
[EN] QUICK START IN 3 STEPS (ALL .EXE - NO SCRIPTS REQUIRED):
------------------------------------------------------------------------
STEP 1: INSTALL
  Double-click "install.exe"
  Automatically sets up Python virtual environment and installs all dependencies.
  (Note: "jarvis.exe" will also automatically run this setup if not yet installed).

STEP 2: CONFIGURE (OPTIONAL)
  Double-click "jarvis-config.exe" (or configure via in-app Settings gear in the HUD)
  Set your LLM Provider, API Key, Base URL (e.g. http://localhost:20128/v1), Model Name.

STEP 3: LAUNCH
  Double-click "jarvis.exe"
  - Microphone is always listening.
  - Call "Jarvis" -> Jarvis responds: "Yes Sir, ada yang bisa saya bantu?"
  - Issue any command:
      * "Jarvis, buka browser" (Opens browser only)
      * "Jarvis, buka chrome lalu cari berita teknologi" (Chained actions)
      * "Jarvis, jam berapa sekarang" / "hari apa ini" (Real-time temporal query)
      * "Jarvis, bagaimana status sistem kamu" (Live hardware telemetry)
      * "Jarvis, buat folder projects_test" (Creates folder)

------------------------------------------------------------------------
[ID] PANDUAN CEPAT DALAM 3 LANGKAH (MURNI .EXE - TANPA BATCH/SCRIPT):
------------------------------------------------------------------------
LANGKAH 1: INSTALASI
  Klik ganda "install.exe"
  Secara otomatis membuat virtual environment Python dan menginstal semua paket.
  (Catatan: "jarvis.exe" juga akan otomatis menjalankan setup jika belum terinstal).

LANGKAH 2: PENGATURAN MODEL AI (OPSIONAL)
  Klik ganda "jarvis-config.exe" (atau gunakan ikon roda gigi ⚙️ di HUD)
  Atur Provider AI, API Key, Base URL lokal/remote, dan Model Name.

LANGKAH 3: JALANKAN
  Klik ganda "jarvis.exe"
  - Mikrofon selalu aktif mendengarkan.
  - Panggil "Jarvis" -> Dijawab: "Yes Sir, ada yang bisa saya bantu?"
  - Berikan perintah apa pun:
      * "Jarvis, buka browser"
      * "Jarvis, buka VSCode di folder JARVIS"
      * "Jarvis, jam berapa sekarang"
      * "Jarvis, cek status sistem"
  - Jika terjadi eror koneksi API AI, eror akan dimunculkan senyap di Recent Activity tanpa dibaca bersuara keras.

------------------------------------------------------------------------
BERKAS DALAM PAKET / PACKAGE FILES:
  jarvis.exe          -> Peluncur utama native Windows (Main native launcher)
  install.exe         -> Pemasang dependensi native Windows (Native installer)
  jarvis-config.exe   -> Utilitas konfigurasi AI GUI Windows (Native settings)
  backend/            -> Mesin AI Python, database SQLite WAL, audio cache
  frontend/           -> Antarmuka Iron Man Sci-Fi HUD (jarvis-hud.jar)

========================================================================
