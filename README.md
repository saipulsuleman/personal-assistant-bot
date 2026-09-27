# ⚡ AURA: AI Personal Productivity & Life Assistant

> **Final Project: LLM-Based Tools and Gemini API Integration for Data Scientists**  
> *Hacktiv8 Indonesia*

[![Python Version](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![Framework](https://img.shields.io/badge/Framework-Streamlit-FF4B4B.svg)](https://streamlit.io/)
[![AI Model](https://img.shields.io/badge/AI%20Model-Google%20Gemini%20API-4285F4.svg)](https://aistudio.google.com/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

---

## 📌 1. Deskripsi & Latar Belakang Proyek

**AURA (Autonomous Utility & Resilience Assistant)** adalah *chatbot* asisten produktivitas harian berbasis kecerdasan buatan (AI) yang dirancang untuk membantu mahasiswa, data scientist, dan profesional dalam mengatasi *cognitive overload* (kelelahan mental akibat banyaknya tugas, riset, dan jadwal).

AURA bertindak sebagai **Life Copilot interaktif** yang berorientasi pada tindakan nyata (*action-oriented*):
- Menyesuaikan gaya komunikasi dan domain keahlian secara dinamis sesuai kebutuhan kerja pengguna.
- Menyediakan *Daily Morning Briefing* terintegrasi data cuaca *real-time* dari Open-Meteo API.
- Menghasilkan ringkasan agenda terstruktur, prioritas *Eisenhower Matrix*, dan checklist aksi langsung di dalam obrolan.
- Mendukung pemecahan masalah data science, optimasi alur kerja, hingga panduan sesi fokus *Pomodoro*.

---

## ✨ 2. Fitur Utama & Parameter Kreatif

### 🎭 Parameter Kreatif 1: Multi-Persona & Gaya Bahasa
Pengguna dapat memilih karakter asisten sesuai suasana hati atau konteks kerja:
* 💼 **Executive Assistant**: Formal, tajam, padat, berorientasi hasil (*results-driven*), dan minim basa-basi.
* ☕ **Casual Buddy**: Santai, hangat, suportif, dan bersahabat layaknya rekan kerja yang akrab.
* ⏱️ **Productivity Coach**: Disiplin, to-the-point, anti-prokrastinasi, dan berfokus pada eksekusi tugas (*time-blocking* & *Pomodoro*).

### 🎯 Parameter Kreatif 2: Domain Fokus Keahlian
* 🎯 **Manajemen Produktivitas**: Optimasi alur kerja, time-blocking, dan pengorganisasian tugas.
* 💻 **Data Science & Koding**: Konsultasi analitik data, machine learning, Python/SQL, dan debugging.
* 🌿 **Mindset & Work-Life Balance**: Pengelolaan energi, pencegahan burnout, dan kebiasaan positif (*habits*).

### 🎛️ Parameter Kreatif 3: Suhu & Kreativitas (Temperature Slider)
Pengaturan dinamis dari `0.0` hingga `1.0`:
* **0.0 - 0.3 (Strict / Precision)**: Jawaban lebih faktual, terstruktur, dan deterministik (cocok untuk analisis teknis dan prioritas).
* **0.7 - 1.0 (Creative / Brainstorming)**: Jawaban lebih eksploratif, variatif, dan kaya ide (cocok untuk mencari solusi inovatif atau ide proyek).

### 🌤️ Integrasi Tools Eksternal: Live Weather API
* Menggunakan **Open-Meteo Live Weather API** (gratis, tanpa limitasi key) untuk mengambil kondisi cuaca, suhu, dan kecepatan angin kota secara *real-time*.
* Informasi cuaca otomatis disuntikkan (*augmented context*) ke dalam sistem asisten untuk memberikan rekomendasi aktivitas harian yang relevan.

### ⚡ Quick Action Prompts (1-Click)
Tombol jalan pintas untuk kebutuhan rutin harian:
* 🌅 **Morning Briefing**: Rekap rencana dan rekomendasi hari ini berdasarkan cuaca.
* 🎯 **Susun Prioritas Hari Ini**: Evaluasi pekerjaan menggunakan matriks penting vs mendesak (*Eisenhower Matrix*).
* ⏳ **Sesi Pomodoro 25 Menit**: Rencana fokus kerja intensif 25 menit.
* 💡 **Ide Proyek Data Science**: Brainstorming 3 ide proyek data science yang siap diimplementasikan.

### 💾 Memory & Export Sesi
* Mekanisme memori riwayat obrolan *multi-turn* dengan *sliding window buffer*.
* Tombol **Ekspor Percakapan** ke format Markdown (`.md`) untuk dokumentasi atau catatan belajar.

---

## 🏛️ 3. Arsitektur Sistem

```mermaid
graph TD
    User([Pengguna]) --> UI[Streamlit Interactive Modern UI]
    UI --> Sidebar[Sidebar Parameters & Tools]
    Sidebar --> Config[Persona, Domain Fokus, Temperature, Model, Kota]
    
    UI --> MemoryMgr[Session & Memory Manager]
    MemoryMgr --> Context[Sliding Window Context]
    
    UI --> GeminiEngine[Gemini API Client - Dual SDK]
    Config --> GeminiEngine
    Context --> GeminiEngine
    
    GeminiEngine --> Tools[External Tools Engine]
    Tools --> WeatherAPI[Open-Meteo Live Weather API]
    
    GeminiEngine --> StreamingResponse[Streaming Response Stream]
    StreamingResponse --> UI
```

---

## 📂 4. Struktur Direktori Proyek

```
Personal Assistant Bot/
├── .env.example              # Template konfigurasi environment
├── .gitignore                # Mengabaikan file sensitif (.env, venv, pycache)
├── requirements.txt          # Daftar dependencies Python
├── README.md                 # Dokumentasi proyek lengkap
├── app.py                    # Aplikasi utama Streamlit & antarmuka modern
├── core/
│   ├── __init__.py           # Paket modul core
│   ├── config.py             # Definisi persona, domain fokus, prompt, dan quick actions
│   ├── gemini_client.py      # Integrasi Gemini API (Dual SDK: google-genai + fallback)
│   ├── memory.py             # Pengelolaan riwayat pesan & ekspor chat
│   └── tools.py              # Tool cuaca Open-Meteo
└── assets/
    └── ui_screenshot.png     # Tangkapan layar antarmuka aplikasi (< 1MB)
```

---

## 🚀 5. Panduan Instalasi & Menjalankan Aplikasi

### Prasyarat
* Python versi 3.10 atau yang lebih baru.
* Google Gemini API Key (dapat diperoleh secara gratis di [Google AI Studio](https://aistudio.google.com/)).

### Langkah-langkah:

1. **Clone Repositori:**
   ```bash
   git clone https://github.com/<username-anda>/personal-assistant-bot.git
   cd personal-assistant-bot
   ```

2. **Buat & Aktifkan Virtual Environment (Opsional):**
   ```bash
   python -m venv venv
   # Windows:
   venv\Scripts\activate
   # macOS/Linux:
   source venv/bin/activate
   ```

3. **Install Dependensi:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Konfigurasi API Key:**
   Masukkan API key Anda ke file `.env`:
   ```env
   GEMINI_API_KEY=AIzaSy...
   DEFAULT_CITY=Jakarta
   ```
   *(Atau masukkan API Key langsung melalui kolom di sidebar web aplikasi).*

5. **Jalankan Aplikasi:**
   ```bash
   python -m streamlit run app.py
   ```
   Buka peramban (browser) di alamat: `http://localhost:8501`.

---

## 📝 6. Data Pengumpulan Final Project Hacktiv8

| Pertanyaan Google Form | Jawaban |
| :--- | :--- |
| **Nama project** | **AURA: AI Personal Productivity & Life Assistant** |
| **Siapa target pengguna chatbot Anda?** | Mahasiswa, data scientist, dan pekerja profesional yang menghadapi *cognitive overload* dalam mengelola rutinitas harian, jadwal, to-do list, dan membutuhkan pendamping produktivitas adaptif. |
| **Bagaimana chatbot Anda dapat membantu pengguna?** | 1. Mengubah percakapan bahasa alami menjadi aksi nyata (ekstraksi action items, rekomendasi checklist, dan prioritas Eisenhower).<br>2. Menyajikan *Daily Morning Briefing* terintegrasi live cuaca real-time (Open-Meteo API).<br>3. Menyesuaikan gaya komunikasi via persona (*Executive Assistant*, *Casual Buddy*, *Productivity Coach*) serta domain fokus (*Produktivitas*, *Data Science*, *Mindset*).<br>4. Membantu brainstorming & riset teknis dengan kontrol parameter suhu/kreativitas (*creative parameters*).<br>5. Menyimpan memori obrolan multi-turn agar konteks tugas tetap konsisten. |
| **Link Github** | *(Cantumkan link repositori GitHub Anda)* |
| **UI (User Interface) chatbot** | File `assets/ui_screenshot.png` (resolusi tinggi, ukuran < 1 MB). |
| **Izin Publikasi** | **Ya, saya setuju** |

---

## 👨‍💻 Kontributor
* Final Project - LLM-Based Tools and Gemini API Integration for Data Scientists (Hacktiv8 Indonesia).
