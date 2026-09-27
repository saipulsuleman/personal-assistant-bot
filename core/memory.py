"""
Conversation Memory & History Management for AURA Assistant
"""
from typing import List, Dict, Any
import json
import datetime

class MemoryManager:
    """
    Mengelola riwayat obrolan dan context window untuk efisiensi token dan konteks konsisten.
    """
    
    @staticmethod
    def format_history_for_gemini(messages: List[Dict[str, Any]], max_turns: int = 10) -> List[Dict[str, Any]]:
        """
        Memformat riwayat pesan ke format Gemini API (role: 'user' / 'model').
        Membatasi jumlah turn terakhir (sliding window memory).
        """
        gemini_history = []
        recent_messages = messages[-max_turns:] if len(messages) > max_turns else messages
        
        for msg in recent_messages:
            role = "user" if msg["role"] == "user" else "model"
            gemini_history.append({
                "role": role,
                "parts": [msg["content"]]
            })
        return gemini_history

    @staticmethod
    def export_chat_to_markdown(messages: List[Dict[str, Any]], persona_name: str) -> str:
        """
        Mengekspor riwayat percakapan menjadi teks Markdown yang rapi.
        """
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        lines = [
            f"# AURA Assistant - Riwayat Percakapan",
            f"**Waktu Ekspor**: {timestamp}  ",
            f"**Mode Persona**: {persona_name}  ",
            f"---",
            ""
        ]
        
        for i, msg in enumerate(messages, 1):
            sender = "👤 Anda" if msg["role"] == "user" else "🤖 AURA"
            lines.append(f"### {sender}")
            lines.append(f"{msg['content']}\n")
            
        return "\n".join(lines)
