"""
Gemini API Client Wrapper for AURA Assistant
Powered by the official Google GenAI SDK (google-genai) with fallback support.
Supports dynamic system instructions, temperature control, streaming, and error handling.
"""
import os
import warnings
from typing import Generator, List, Dict, Any, Optional

# Coba import SDK resmi terbaru (google-genai)
try:
    from google import genai
    from google.genai import types
    NEW_SDK_AVAILABLE = True
except ImportError:
    NEW_SDK_AVAILABLE = False

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
        model_name: str = "gemini-3.8-flash",
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
        live_context: str = "",
        persona_tag: str = "executive"
    ) -> Generator[str, None, None]:
        """
        Menghasilkan streaming response dari Gemini API dengan system prompt dinamis dan riwayat obrolan.
        """
        if not self.validate_key():
            yield (
                "⚠️ **API Key Gemini belum diisi.**\n\n"
                "Silakan dapatkan API key gratis di [Google AI Studio](https://aistudio.google.com/) "
                "dan masukkan ke kolom di bilah sisi (sidebar)."
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
                        yield "❌ **Kunci API tidak valid.** Pastikan API Key yang Anda salin dari Google AI Studio sudah sesuai."
                        return
                    if "quota" in err_msg.lower() or "resourceexhausted" in err_msg.lower():
                        yield "⚠️ **Batas kuota API tercapai.** Silakan tunggu beberapa detik sebelum mencoba kembali."
                        return
                    # Jika 404 / model tidak ditemukan, lanjut mencoba model cadangan berikutnya
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
            "💡 *Saran*: Pastikan Anda memilih model **`gemini-3.8-flash`** atau **`gemini-3.5-flash-lite`** pada dropdown Model AI di sidebar."
        )
