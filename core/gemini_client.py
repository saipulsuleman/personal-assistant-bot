"""
Gemini API Client Wrapper for AURA Assistant
Powered by the official Google GenAI SDK (google-genai) with fallback support.
Also includes a built-in Intelligent Demo/Simulation Engine for testing without an API key.
"""
import os
import time
from typing import Generator, List, Dict, Any, Optional

# Coba import SDK resmi terbaru (google-genai)
try:
    from google import genai
    from google.genai import types
    NEW_SDK_AVAILABLE = True
except ImportError:
    NEW_SDK_AVAILABLE = False

import warnings
warnings.filterwarnings("ignore", category=FutureWarning)

# Fallback ke google-generativeai jika diperlukan
try:
    import google.generativeai as legacy_genai
    from google.generativeai.types import GenerationConfig
    LEGACY_SDK_AVAILABLE = True
except ImportError:
    LEGACY_SDK_AVAILABLE = False


class GeminiAssistantClient:
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_name: str = "gemini-1.5-flash",
        temperature: float = 0.7,
        demo_mode: bool = False
    ):
        self.api_key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()
        self.model_name = model_name
        self.temperature = float(temperature)
        self.demo_mode = demo_mode
        self.client = None

        if not self.demo_mode and self.validate_key() and NEW_SDK_AVAILABLE:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception:
                self.client = None
        elif not self.demo_mode and self.validate_key() and LEGACY_SDK_AVAILABLE:
            try:
                legacy_genai.configure(api_key=self.api_key)
            except Exception:
                pass

    def validate_key(self) -> bool:
        """Mengecek apakah format API key terisi."""
        return bool(self.api_key and len(self.api_key) > 10)

    def generate_chat_stream(
        self,
        prompt: str,
        system_instruction: str,
        history: Optional[List[Dict[str, Any]]] = None,
        live_context: str = "",
        persona_tag: str = "executive"
    ) -> Generator[str, None, None]:
        """
        Menghasilkan streaming response dari Gemini API atau Demo Engine.
        """
        # JIKA DALAM MODE DEMO / SIMULASI
        if self.demo_mode:
            yield from self._generate_simulated_stream(prompt, persona_tag, live_context)
            return

        # JIKA API KEY KOSONG
        if not self.validate_key():
            yield (
                "⚠️ **API Key Gemini belum diisi.**\n\n"
                "Anda dapat:\n"
                "1. **Aktifkan 'Mode Demo'** pada bilah sisi (sidebar) untuk mencoba bot langsung tanpa API key.\n"
                "2. Atau dapatkan API key gratis di [Google AI Studio](https://aistudio.google.com/) (1-2 menit, tanpa kartu kredit) lalu tempel di sidebar."
            )
            return

        augmented_instruction = system_instruction
        if live_context:
            augmented_instruction += (
                f"\n\n[KONTEKS REAL-TIME PENGGUNA]:\n{live_context}\n"
                "Gunakan konteks ini secara proaktif jika relevan dengan pertanyaan atau sapaan pengguna."
            )

        candidate_models = list(dict.fromkeys([
            self.model_name,
            "gemini-3.8-flash",
            "gemini-3.5-flash-lite",
            "gemini-2.5-flash",
            "gemini-3.1-pro",
            "gemini-1.5-flash-latest",
            "gemini-1.5-flash"
        ]))

        last_error = ""

        # 1. Menggunakan SDK Baru (google-genai)
        if NEW_SDK_AVAILABLE and self.client:
            contents = []
            if history:
                for item in history:
                    role = "user" if item.get("role") == "user" else "model"
                    text_val = item.get("content", "")
                    if text_val:
                        contents.append(
                            types.Content(
                                role=role,
                                parts=[types.Part.from_text(text=text_val)]
                            )
                        )
            contents.append(
                types.Content(
                    role="user",
                    parts=[types.Part.from_text(text=prompt)]
                )
            )

            config = types.GenerateContentConfig(
                system_instruction=augmented_instruction,
                temperature=self.temperature,
                max_output_tokens=2048,
            )

            for cand_model in candidate_models:
                try:
                    response_stream = self.client.models.generate_content_stream(
                        model=cand_model,
                        contents=contents,
                        config=config
                    )

                    streamed_any = False
                    for chunk in response_stream:
                        if chunk.text:
                            streamed_any = True
                            yield chunk.text
                    
                    if streamed_any:
                        return
                except Exception as e:
                    err_msg = str(e)
                    last_error = err_msg
                    if "API_KEY_INVALID" in err_msg or "invalid api key" in err_msg.lower():
                        yield "❌ **Kunci API tidak valid.** Silakan salin ulang API Key yang benar dari Google AI Studio atau aktifkan Mode Demo."
                        return
                    if "quota" in err_msg.lower() or "resourceexhausted" in err_msg.lower():
                        yield "⚠️ **Batas kuota API tercapai.** Silakan tunggu beberapa detik atau gunakan Mode Demo."
                        return
                    # Jika 404 / model tidak ditemukan, lanjut mencoba model berikutnya di daftar kandidat
                    continue

        # 2. Fallback SDK Legacy (google-generativeai)
        if LEGACY_SDK_AVAILABLE:
            try:
                legacy_genai.configure(api_key=self.api_key)
                gen_config = GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=2048,
                )
                chat_history = []
                if history:
                    for item in history:
                        role = "user" if item.get("role") == "user" else "model"
                        chat_history.append({
                            "role": role,
                            "parts": [item.get("content", "")]
                        })

                for cand_model in candidate_models:
                    try:
                        model = legacy_genai.GenerativeModel(
                            model_name=cand_model,
                            system_instruction=augmented_instruction,
                            generation_config=gen_config
                        )
                        chat = model.start_chat(history=chat_history)
                        response = chat.send_message(prompt, stream=True)
                        streamed_any = False
                        for chunk in response:
                            if chunk.text:
                                streamed_any = True
                                yield chunk.text
                        if streamed_any:
                            return
                    except Exception as e:
                        last_error = str(e)
                        continue
            except Exception as e:
                last_error = str(e)

        # Jika seluruh model kandidat gagal diakses
        yield (
            f"❌ **Koneksi Model Gagal**: `{last_error}`\n\n"
            "💡 *Saran Solusi*:\n"
            "1. Google AI Studio sering memperbarui daftar model aktif. Silakan pilih model **`gemini-3.8-flash`** atau **`gemini-3.5-flash-lite`** pada dropdown Model AI di sidebar.\n"
            "2. Atau aktifkan **`🧪 Mode Demo (Tanpa API Key)`** di sidebar untuk menjalankan simulasi tanpa hambatan."
        )

    def _generate_simulated_stream(
        self,
        prompt: str,
        persona_tag: str,
        live_context: str
    ) -> Generator[str, None, None]:
        """
        Simulated engine untuk mendemonstrasikan kapabilitas AURA tanpa koneksi API Key.
        """
        p_lower = prompt.lower()
        
        # Ekstrak cuaca dari context jika ada
        weather_info = "Cuaca saat ini cukup cerah."
        if "cuaca:" in live_context.lower():
            for line in live_context.split("\n"):
                if "cuaca:" in line.lower():
                    weather_info = line.replace("- Cuaca:", "").strip()

        # Respon cerdas berdasarkan Prompt & Persona
        if "morning" in p_lower or "briefing" in p_lower:
            if persona_tag == "executive":
                text = (
                    "**[EXECUTIVE BRIEFING HARIAN]**\n\n"
                    f"📊 **Kondisi Lingkungan**: {weather_info}\n\n"
                    "📌 **Prioritas Agenda Hari Ini**:\n"
                    "1. **Tinjau Milestone Proyek**: Selesaikan item yang tertunda pada to-do list aktif.\n"
                    "2. **Blok Fokus Kerja (Deep Work)**: Alokasikan 90 menit tanpa distraksi sebelum jam makan siang.\n"
                    "3. **Evaluasi Output**: Ukur pencapaian utama di penghujung hari.\n\n"
                    "Apa keputusan atau target pertama yang ingin Anda eksekusi pagi ini?"
                )
            elif persona_tag == "coach":
                text = (
                    "🔥 **BANGUN & EKSEKUSI! Briefing Pagi AURA**\n\n"
                    f"🌤️ **Update Cuaca**: {weather_info}\n\n"
                    "Hari ini bukan hari untuk menunda pekerjaan! Berikut game plan kita:\n"
                    "- **Langkah 1**: Ambil 1 tugas paling berat (*Eat the Frog*) dari daftar to-do Anda sekarang.\n"
                    "- **Langkah 2**: Nyalakan timer Pomodoro 25 menit pertama. Singkirkan HP dan tab sosmed.\n"
                    "- **Langkah 3**: Jangan berhenti sebelum lonceng 25 menit berbunyi!\n\n"
                    "Tuliskan apa tugas nomor satu yang akan Anda hajar sekarang juga!"
                )
            else: # casual
                text = (
                    "Selamat pagi! ☕ Semangat buat hari ini ya!\n\n"
                    f"Ngomong-ngomong, {weather_info}. Enak banget suasananya buat mulai hari dengan tenang.\n\n"
                    "Rencana seru apa nih yang mau kamu beresin hari ini? "
                    "Kalau bingung mulai dari mana, coba cek to-do list di sidebar atau pilih tugas yang paling ringan dulu buat pemanasan!"
                )
        elif "prioritas" in p_lower or "eisenhower" in p_lower:
            if persona_tag == "executive":
                text = (
                    "**[ANALISIS PRIORITAS - EISENHOWER MATRIX]**\n\n"
                    "Berdasarkan metodologi manajemen waktu eksekutif, mari klasifikasikan tugas Anda:\n\n"
                    "1. 🔴 **Penting & Mendesak (Do First)**:\n"
                    "   - *Tugas dengan deadline hari ini dan dampak tinggi pada deliverables.*\n"
                    "2. 🔵 **Penting tapi Tidak Mendesak (Schedule)**:\n"
                    "   - *Peningkatan skill data science, perancangan arsitektur, dan riset.*\n"
                    "3. 🟡 **Mendesak tapi Kurang Penting (Delegate/Minimize)**:\n"
                    "   - *Notifikasi obrolan cepat, pesan admin rutin.*\n"
                    "4. ⚪ **Tidak Penting & Tidak Mendesak (Eliminate)**:\n"
                    "   - *Scrolling tanpa tujuan, multitasking berlebih.*\n\n"
                    "Sebutkan 3 tugas utama Anda saat ini agar saya bantu petakan ke kuadran yang tepat."
                )
            elif persona_tag == "coach":
                text = (
                    "🎯 **FOKUS PADA HASIL, BUKAN KESIBUKAN SEMU!**\n\n"
                    "Banyak orang sibuk seharian tapi tidak menghasilkan apa-apa karena salah memilih prioritas.\n"
                    "Terapkan aturan **80/20 (Pareto Principle)**:\n"
                    "- 20% tugas Anda akan menghasilkan 80% dampak terbesar Anda hari ini.\n\n"
                    "Coba tengok To-Do List di samping kiri. Dari semua tugas itu, **mana SATU tugas yang jika selesai hari ini membuat Anda merasa sangat puas?** Kerjakan itu duluan!"
                )
            else: # casual
                text = (
                    "Yuk kita sortir bareng biar kepalamu nggak pusing! 💆‍♂️\n\n"
                    "Kadang kalau tugas numpuk, kita berasa pengen ngerjain semuanya sekaligus. Padahal kuncinya gampang:\n"
                    "- Pilih 1 hal wajib kelar hari ini.\n"
                    "- Pilih 2 hal pelengkap kalau ada sisa waktu.\n"
                    "- Sisanya simpan buat besok aja, jangan dipaksain!\n\n"
                    "Coba ceritain, tugas apa yang paling bikin kamu kepikiran sekarang?"
                )
        elif "pomodoro" in p_lower or "25 menit" in p_lower:
            text = (
                "⏱️ **RENCANA SESI FOKUS 25 MENIT (POMODORO TECHNIQUE)**\n\n"
                "1. **Tentukan 1 Target Spesifik**: Misal: *Selesaikan penulisan fungsi ekstraksi data*.\n"
                "2. **Eliminasi Distraksi**: Tutup browser tab yang tidak relevan, senyapkan ponsel.\n"
                "3. **Fokus Total**: Kerja intensif selama 25 menit ke depan tanpa beralih aplikasi.\n"
                "4. **Istirahat 5 Menit**: Berdiri, minum air putih, regangkan otot.\n\n"
                "Sesi Pomodoro Anda siap dimulai! Klik centang pada to-do list setelah sesi ini berhasil diselesaikan. 🚀"
            )
        elif "data science" in p_lower or "ide" in p_lower:
            text = (
                "💡 **3 IDE PROYEK INOVATIF TOOLS AI & DATA SCIENCE**\n\n"
                "1. **Smart Resume & Job Fit Analyzer (Gemini Vision + Text)**\n"
                "   - Mengunggah CV (PDF/Gambar) dan mengekstrak kecocokan terhadap deskripsi pekerjaan data science dengan scoring dan saran perbaikan.\n\n"
                "2. **Automated EDA & Insights Generator**\n"
                "   - Input dataset CSV, lalu Gemini otomatis menghasilkan rangkuman korelasi, anomali statistik, dan visualisasi interaktif.\n\n"
                "3. **Multi-Agent Productivity Copilot (Seperti AURA!)**\n"
                "   - Bot asisten yang mengintegrasikan Function Calling, Live Weather API, dan Context Memory untuk otomasi harian.\n\n"
                "Tertarik untuk mendalami salah satu ide di atas untuk pengembangan portofolio Anda?"
            )
        else:
            text = (
                f"Saya memahami pesan Anda: *\"{prompt}\"*.\n\n"
                f"Dalam mode **{persona_tag.capitalize()}**, saya siap membantu merapikan alur kerja Anda, mengevaluasi to-do list, atau mendiskusikan topik teknis data science.\n\n"
                f"💡 *Tips*: Anda bisa mencoba tombol aksi cepat seperti **Morning Briefing**, **Prioritaskan Tugas**, atau **Pomodoro** untuk melihat kapabilitas integrasi sistem ini."
            )

        # Efek typing streaming yang realistis
        chunks = text.split(" ")
        for i in range(0, len(chunks), 3):
            sub_chunk = " ".join(chunks[i:i+3]) + " "
            time.sleep(0.04)
            yield sub_chunk
