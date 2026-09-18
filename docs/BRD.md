# Business Requirement Document (BRD)
**Project Name:** J.A.R.V.I.S. (Autonomous OS Voice Agent)  
**Version:** 1.0.0  
**Status:** Approved  
**Author:** Mohamad Fiky Ba'dafitro  
**Document Owner:** Engineering & Product Team  

---

## 1. Project Background & Business Opportunity
Perkembangan model AI dan automasi berbasis agen (*agentic workflows*) membuka peluang untuk mengubah cara pengguna berinteraksi dengan komputer personal. Saat ini, mayoritas alat bantu automasi desktop mengharuskan pengguna berinteraksi lewat terminal atau teks terpisah, minim interaksi verbal yang imersif, dan rentan terhadap risiko keamanan jika diberi hak kontrol sistem operasi.

J.A.R.V.I.S. hadir untuk menjembatani interaksi manusia-komputer secara *hands-free* penuh melalui suara, menghadirkan antarmuka grafis futuristik modern (Iron Man HUD), serta mengotomatisasi aktivitas pengetikan dan navigasi OS secara aman dengan *guardrails* ketat.

---

## 2. Business Objectives & Success Metrics (KPIs)

### 2.1 Business Objectives
* Menyediakan asisten virtual desktop mandiri (*stand-alone*) yang fleksibel terhadap berbagai penyedia model AI (BYO-API).
* Meningkatkan efisiensi kerja pengguna melalui automasi tugas berulang (navigasi, pengetikan, pencarian web).
* Menjaga integritas dan privasi data lokal pengguna tanpa risiko kebocoran data rahasia (*zero data leak incident*).

### 2.2 Key Performance Indicators (KPIs)
* **Voice Latency Response:** Waktu respons dari akhir ucapan pengguna hingga sistem mulai berbicara maksimal < 1,5 detik.
* **Context Recovery Rate:** 100% riwayat konteks tersimpan dan dapat dimuat kembali setelah skenario *power cut/abrupt termination*.
* **Safety Violation Catch Rate:** 100% deteksi dan pemutusan otomatis (*auto-abort*) terhadap upaya akses data sensitif (PII) atau instruksi perusak OS.
* **Concurrent Communication:** 0% *thread lock* (pengguna tetap dapat berkomunikasi dengan suara saat automasi layar berjalan).

---

## 3. Stakeholders & User Personas

### 3.1 Key Stakeholders
* **System Architect & Lead Developer:** Penanggung jawab keandalan integrasi JavaFX, FastAPI, model speech, dan SQLite.
* **Security & Compliance Lead:** Pengawas kepatuhan terhadap batasan privasi data (PII) dan isolasi eksekusi sistem operasi.
* **End-User / Developer / Power User:** Pengguna utama yang memerlukan automasi layar dan kontrol *hands-free*.

### 3.2 User Persona
* **Nama:** Power User / Developer
* **Kebutuhan:** Membutuhkan asisten yang dapat mengetik, mencari informasi, membuka aplikasi, dan merespons via suara saat tangan sibuk mengerjakan tugas lain.
* **Pain Points:** Khawatir AI mengakses email/password pribadi, UI asisten konvensional membosankan, dan sistem lambat saat melakukan banyak proses sekaligus.

---

## 4. Scope of Work (Ruang Lingkup)

### 4.1 In-Scope
* Implementasi GUI futuristik bertema Iron Man HUD menggunakan JavaFX (Arc Reactor, audio waveform, system metrics, input console).
* Fitur sapaan suara proaktif otomatis saat aplikasi pertama kali dijalankan.
* Dukungan multi-model LLM (OpenAI, Gemini, Ollama, dll.) dengan antarmuka input API Key manual.
* Kontrol navigasi OS lintas platform (Windows & Linux): pergerakan kursor, klik, pengetikan keyboard berkecepatan alami, dan akses kamera.
* Penyimpanan konteks real-time menggunakan basis data lokal SQLite (WAL mode).
* Arsitektur konkuren (asinkron) agar suara tetap aktif saat task navigasi OS berlangsung.
* Mekanisme *Security Guardrail*, *Auto-Abort*, dan *Hardware Fail-Safe* (kill switch).

### 4.2 Out-of-Scope
* Akses atau penyimpanan kredensial pribadi pengguna (email, kata sandi, rekening, kontak personal).
* Modifikasi file konfigurasi inti sistem operasi (misal: registri root, folder `/etc`, `C:\Windows\System32`).
* Aksi otonom tanpa adanya *trigger* eksplisit dari pengguna.
* Integrasi *cloud storage syncing* pihak ketiga untuk konteks percakapan (semua wajib lokal).

---

## 5. Business Rules & Compliance Requirements

| Rule ID | Nama Kebijakan | Deskripsi Aturan Bisnis |
| :--- | :--- | :--- |
| **BR-01** | **Explicit Trigger Only** | Sistem dilarang memulai task otomatisasi apa pun tanpa adanya perintah suara atau teks yang jelas dari pengguna. |
| **BR-02** | **Privacy Protection Mandate** | Sistem dilarang membaca, mengekstrak, atau mengetikkan informasi identitas pribadi (email, password, nomor telepon, alamat). Pelanggaran langsung memicu pembatalan task (*kill-switch*). |
| **BR-03** | **OS Integrity Preservation** | Sistem dilarang menjalankan perintah yang merusak integritas OS (`format`, penghapusan sistem). |
| **BR-04** | **Data Sovereignty** | Konteks percakapan dan status memori sepenuhnya milik pengguna dan disimpan secara lokal tanpa telemetri eksternal. |
| **BR-05** | **User Override Priority** | Tindakan pengguna di perangkat fisik (misal: menarik mouse ke sudut layar) memiliki prioritas mutlak di atas instruksi agen. |

---

## 6. Risk Assessment & Mitigation Strategy

* **Risiko 1: Kegagalan LLM (Halusinasi Perintah OS Berbahaya)**
  * *Mitigasi:* Menggunakan lapisan validasi *Security Guardrail* di Python yang memfilter setiap payload JSON aksi sebelum diteruskan ke `pyautogui`.
* **Risiko 2: Kerusakan Basis Data Akibat Pemadaman Mendadak**
  * *Mitigasi:* Mengonfigurasi SQLite dengan mode WAL (*Write-Ahead Logging*) dan transaksi *atomic* untuk menjamin data tidak *corrupt*.
* **Risiko 3: Latensi Suara Tinggi Menurunkan UX**
  * *Mitigasi:* Memanfaatkan Faster-Whisper dan Edge-TTS yang dioptimasi untuk transmisi *low-latency* via WebSocket lokal.
* **Risiko 4: Pembekuan UI saat Menjalankan Perintah Berat**
  * *Mitigasi:* Pemisahan tegas arsitektur klien-server via WebSocket: JavaFX murni menangani *rendering/audio*, Python menangani *heavy processing*.

---

## 7. Assumptions & Dependencies

### 7.1 Asumsi
* Pengguna memiliki mikrofon dan speaker fungsional untuk interaksi audio dua arah.
* Sistem operasi host mengizinkan hak akses *Accessibility* / *Input Automation* untuk kontrol mouse dan keyboard.

### 7.2 Dependensi
* Java SE Development Kit (JDK) 21 LTS dan OpenJFX 21.
* Python 3.12 dengan pustaka FastAPI, PyAutoGUI, Pynput, OpenCV, dan SQLite3.
* Akses jaringan hanya diperlukan untuk API LLM eksternal (jika tidak menggunakan LLM lokal) dan layanan Edge-TTS.

---

## 8. Sign-off & Approval

| Role | Nama | Tanggal | Status |
| :--- | :--- | :--- | :--- |
| System Architect & Lead | Mohamad Fiky Ba'dafitro | 18 September 2026 | Approved |
| Security Reviewer | System Safety Guardrail | 18 September 2026 | Approved |