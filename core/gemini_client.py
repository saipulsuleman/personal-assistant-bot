"""
Gemini API Client Wrapper for AURA Assistant
Powered by the official Google GenAI SDK (google-genai) with fallback support.
Supports dynamic system instructions, temperature control, streaming, and error handling.
"""
import os
from typing import Generator, List, Dict, Any, Optional

# Coba import SDK resmi terbaru (google-genai)
try:
    from google import genai
    from google.genai import types
    NEW_SDK_AVAILABLE = True
except ImportError:
    NEW_SDK_AVAILABLE = False

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
        temperature: float = 0.7
    ):
        self.api_key = (api_key or os.getenv("GEMINI_API_KEY", "")).strip()
        self.model_name = model_name
        self.temperature = float(temperature)
        self.client = None

        if self.validate_key() and NEW_SDK_AVAILABLE:
            try:
                self.client = genai.Client(api_key=self.api_key)
            except Exception:
                self.client = None
        elif self.validate_key() and LEGACY_SDK_AVAILABLE:
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
        live_context: str = ""
    ) -> Generator[str, None, None]:
        """
        Menghasilkan streaming response dari Gemini API dengan system prompt dinamis dan riwayat obrolan.
        """
        if not NEW_SDK_AVAILABLE and not LEGACY_SDK_AVAILABLE:
            yield "❌ Pustaka Google GenAI belum terinstal. Silakan jalankan `pip install -r requirements.txt`."
            return

        if not self.validate_key():
            yield (
                "⚠️ **API Key Gemini belum diisi.**\n\n"
                "Untuk mulai menggunakan asisten AURA:\n"
                "1. Dapatkan API key gratis di [Google AI Studio](https://aistudio.google.com/).\n"
                "2. Masukkan API key pada kolom di sidebar sebelah kiri, atau simpan ke file `.env` (`GEMINI_API_KEY=AIzaSy...`)."
            )
            return

        # Gabungkan konteks real-time (cuaca, to-do list aktif)
        augmented_instruction = system_instruction
        if live_context:
            augmented_instruction += (
                f"\n\n[KONTEKS REAL-TIME PENGGUNA]:\n{live_context}\n"
                "Gunakan konteks ini secara proaktif jika relevan dengan pertanyaan atau sapaan pengguna."
            )

        # 1. Menggunakan SDK Baru (google-genai)
        if NEW_SDK_AVAILABLE and self.client:
            try:
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

                response_stream = self.client.models.generate_content_stream(
                    model=self.model_name,
                    contents=contents,
                    config=config
                )

                for chunk in response_stream:
                    if chunk.text:
                        yield chunk.text
                return
            except Exception as e:
                err_msg = str(e)
                if "API_KEY_INVALID" in err_msg or "invalid api key" in err_msg.lower():
                    yield "❌ **Kunci API tidak valid.** Pastikan Anda menyalin API Key yang benar dari Google AI Studio."
                    return
                elif "quota" in err_msg.lower() or "resourceexhausted" in err_msg.lower():
                    yield "⚠️ **Batas kuota API tercapai.** Silakan tunggu beberapa detik dan coba kembali."
                    return
                # Jika model tidak ditemukan di google-genai, coba fallback ke legacy

        # 2. Fallback SDK Legacy (google-generativeai)
        if LEGACY_SDK_AVAILABLE:
            try:
                legacy_genai.configure(api_key=self.api_key)
                gen_config = GenerationConfig(
                    temperature=self.temperature,
                    max_output_tokens=2048,
                )
                model = legacy_genai.GenerativeModel(
                    model_name=self.model_name,
                    system_instruction=augmented_instruction,
                    generation_config=gen_config
                )
                chat_history = []
                if history:
                    for item in history:
                        role = "user" if item.get("role") == "user" else "model"
                        chat_history.append({
                            "role": role,
                            "parts": [item.get("content", "")]
                        })
                chat = model.start_chat(history=chat_history)
                response = chat.send_message(prompt, stream=True)
                for chunk in response:
                    if chunk.text:
                        yield chunk.text
            except Exception as e:
                yield f"❌ Terjadi kesalahan saat memproses permintaan: `{str(e)}`"
