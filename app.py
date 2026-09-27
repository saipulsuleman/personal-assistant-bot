"""
AURA - AI Personal Productivity & Life Assistant
Final Project: LLM-Based Tools and Gemini API Integration for Data Scientists (Hacktiv8)
"""
import os
import warnings
warnings.filterwarnings("ignore")

import streamlit as st
from dotenv import load_dotenv

# Import internal modules
from core.config import (
    APP_NAME,
    APP_SUBTITLE,
    APP_TAGLINE,
    PERSONAS,
    QUICK_ACTIONS,
    AVAILABLE_MODELS
)
from core.tools import get_live_weather, TaskManager
from core.memory import MemoryManager
from core.gemini_client import GeminiAssistantClient

# Load environment variables
load_dotenv()

# Konfigurasi Halaman Streamlit
st.set_page_config(
    page_title=f"{APP_NAME} - Personal Assistant Bot",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom Styling (Dark Glassmorphic & Modern Data Science Theme)
CUSTOM_CSS = """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Main Container Padding */
    .block-container {
        padding-top: 1.8rem;
        padding-bottom: 2rem;
        max-width: 1200px;
    }

    /* Header Banner */
    .aura-header {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.7) 0%, rgba(15, 23, 42, 0.9) 100%);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 16px;
        padding: 1.5rem 1.8rem;
        margin-bottom: 1.5rem;
        backdrop-filter: blur(12px);
        box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.3), 0 8px 10px -6px rgba(0, 0, 0, 0.3);
        display: flex;
        align-items: center;
        justify-content: space-between;
    }

    .aura-title-group h1 {
        font-size: 1.85rem;
        font-weight: 700;
        background: linear-gradient(90deg, #38BDF8 0%, #818CF8 50%, #C084FC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        line-height: 1.2;
    }

    .aura-title-group p {
        font-size: 0.92rem;
        color: #94A3B8;
        margin: 0.25rem 0 0 0;
    }

    .aura-badge-container {
        display: flex;
        gap: 0.6rem;
        flex-wrap: wrap;
    }

    .aura-badge {
        font-size: 0.75rem;
        font-weight: 600;
        padding: 0.35rem 0.75rem;
        border-radius: 9999px;
        background: rgba(99, 102, 241, 0.15);
        border: 1px solid rgba(129, 140, 248, 0.3);
        color: #A5B4FC;
        display: inline-flex;
        align-items: center;
        gap: 0.35rem;
    }

    .aura-badge.green {
        background: rgba(16, 185, 129, 0.15);
        border-color: rgba(52, 211, 153, 0.3);
        color: #6EE7B7;
    }

    /* Quick Action Cards */
    .quick-action-header {
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        color: #64748B;
        margin-bottom: 0.6rem;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: #0F172A;
        border-right: 1px solid rgba(255, 255, 255, 0.06);
    }

    .sidebar-section-title {
        font-size: 0.78rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.08em;
        color: #94A3B8;
        margin-top: 1.2rem;
        margin-bottom: 0.5rem;
        display: flex;
        align-items: center;
        gap: 0.4rem;
    }

    .weather-card {
        background: rgba(30, 41, 59, 0.5);
        border: 1px solid rgba(56, 189, 248, 0.2);
        border-radius: 12px;
        padding: 0.9rem;
        margin-bottom: 0.8rem;
    }

    .weather-temp {
        font-size: 1.6rem;
        font-weight: 700;
        color: #38BDF8;
    }

    .weather-desc {
        font-size: 0.82rem;
        color: #CBD5E1;
        margin-top: 0.2rem;
    }

    /* Chat Messages Styling */
    .stChatMessage {
        border-radius: 14px;
        padding: 0.75rem 1rem;
        margin-bottom: 0.75rem;
    }

    /* Footer text */
    .footer-note {
        text-align: center;
        font-size: 0.75rem;
        color: #475569;
        margin-top: 2rem;
    }
</style>
"""
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# Inisialisasi Session State
if "messages" not in st.session_state:
    st.session_state.messages = [
        {
            "role": "model",
            "content": (
                "Halo! Saya **AURA**, asisten produktivitas & *life copilot* Anda. ⚡\n\n"
                "Saya dapat membantu Anda mengelola agenda, membuat to-do list interaktif, "
                "meringkas materi data science, hingga merancang sesi fokus harian. "
                "Pilih persona yang Anda inginkan di bilah sisi atau klik tombol aksi cepat di bawah untuk memulai!"
            )
        }
    ]

if "tasks" not in st.session_state:
    st.session_state.tasks = TaskManager.create_initial_tasks()

if "weather_cache" not in st.session_state:
    default_city = os.getenv("DEFAULT_CITY", "Jakarta")
    st.session_state.weather_cache = get_live_weather(default_city)

if "quick_prompt_input" not in st.session_state:
    st.session_state.quick_prompt_input = None


# ==========================================
# SIDEBAR KONTROL & PARAMETER KREATIF
# ==========================================
with st.sidebar:
    st.markdown("### ⚙️ Konfigurasi & Tools")
    
    # 1. API Key Input
    env_api_key = os.getenv("GEMINI_API_KEY", "")
    api_key_input = st.text_input(
        "Gemini API Key",
        value=env_api_key if env_api_key else "",
        type="password",
        placeholder="AIzaSy...",
        help="Dapatkan API Key gratis di Google AI Studio (aistudio.google.com)"
    )

    if not api_key_input:
        st.warning("⚠️ Masukkan Gemini API Key untuk memulai obrolan.")
    else:
        st.caption("🟢 API Key siap digunakan")

    st.markdown('<div class="sidebar-section-title">🎭 Parameter Kreatif</div>', unsafe_allow_html=True)

    # 2. Persona Selector
    selected_persona_name = st.selectbox(
        "Pilih Persona & Gaya Komunikasi:",
        options=list(PERSONAS.keys()),
        index=0,
        help="Mengubah karakter dan cara asisten merespons pesan Anda."
    )
    current_persona = PERSONAS[selected_persona_name]
    st.info(f"**Gaya**: {current_persona['description']}")

    # 3. Model & Suhu (Creativity / Temperature)
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        selected_model = st.selectbox(
            "Model AI:",
            options=AVAILABLE_MODELS,
            index=0
        )
    with col_m2:
        temp_val = st.slider(
            "Temperature:",
            min_value=0.0,
            max_value=1.0,
            value=0.7,
            step=0.1,
            help="Nilai rendah = lebih faktual & terstruktur. Nilai tinggi = lebih kreatif & eksploratif."
        )

    # 4. Live Weather Integration (External Tool)
    st.markdown('<div class="sidebar-section-title">🌤️ Live Weather Briefing</div>', unsafe_allow_html=True)
    city_col1, city_col2 = st.columns([3, 1])
    with city_col1:
        city_query = st.text_input("Kota:", value="Jakarta", label_visibility="collapsed")
    with city_col2:
        if st.button("🔄", help="Cek Cuaca Terkini"):
            st.session_state.weather_cache = get_live_weather(city_query)

    weather_data = st.session_state.weather_cache
    if weather_data.get("success"):
        st.markdown(
            f"""
            <div class="weather-card">
                <div style="display: flex; justify-content: space-between; align-items: baseline;">
                    <span style="font-weight: 600; color: #F8FAFC;">{weather_data['city']}, {weather_data['country']}</span>
                    <span class="weather-temp">{weather_data['temperature']}°C</span>
                </div>
                <div class="weather-desc">{weather_data['condition']} • Angin {weather_data['wind_speed']} km/h</div>
            </div>
            """,
            unsafe_allow_html=True
        )
    else:
        st.caption(f"Info cuaca: {weather_data.get('message', 'Tidak tersedia')}")

    # 5. Interactive Task Manager (To-Do List)
    st.markdown('<div class="sidebar-section-title">📋 To-Do List Harian</div>', unsafe_allow_html=True)
    
    # Checkbox items
    for task in st.session_state.tasks:
        checked = st.checkbox(task["task"], value=task["completed"], key=f"task_{task['id']}")
        task["completed"] = checked

    # Form tambah tugas baru
    with st.form("new_task_form", clear_on_submit=True):
        new_task_desc = st.text_input("Tambah tugas baru:", placeholder="Misal: Siapkan materi slide...")
        submitted = st.form_submit_button("➕ Tambah Tugas")
        if submitted and new_task_desc.strip():
            new_id = max([t["id"] for t in st.session_state.tasks], default=0) + 1
            st.session_state.tasks.append({"id": new_id, "task": new_task_desc.strip(), "completed": False})
            st.rerun()

    # 6. Session Controls & Export
    st.markdown('<div class="sidebar-section-title">💾 Manajemen Sesi</div>', unsafe_allow_html=True)
    col_s1, col_s2 = st.columns(2)
    with col_s1:
        if st.button("🗑️ Reset Chat", use_container_width=True):
            st.session_state.messages = [st.session_state.messages[0]]
            st.rerun()
    with col_s2:
        chat_markdown = MemoryManager.export_chat_to_markdown(
            st.session_state.messages,
            selected_persona_name
        )
        st.download_button(
            label="📥 Ekspor",
            data=chat_markdown,
            file_name="aura_chat_history.md",
            mime="text/markdown",
            use_container_width=True
        )


# ==========================================
# HEADER UTAMA APLIKASI
# ==========================================
st.markdown(
    f"""
    <div class="aura-header">
        <div class="aura-title-group">
            <h1>⚡ {APP_NAME} <span style="font-size: 1.1rem; color: #94A3B8; font-weight: 500;">| {APP_SUBTITLE}</span></h1>
            <p>{APP_TAGLINE}</p>
        </div>
        <div class="aura-badge-container">
            <span class="aura-badge green">● Model: {selected_model}</span>
            <span class="aura-badge">{selected_persona_name}</span>
            <span class="aura-badge">Temp: {temp_val}</span>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)


# ==========================================
# QUICK ACTION PROMPTS (1-CLICK)
# ==========================================
st.markdown('<div class="quick-action-header">⚡ Aksi Cepat / Template Prompt</div>', unsafe_allow_html=True)
cols = st.columns(len(QUICK_ACTIONS))
for idx, action in enumerate(QUICK_ACTIONS):
    with cols[idx]:
        if st.button(f"{action['icon']} {action['label']}", use_container_width=True, key=f"qa_{idx}"):
            st.session_state.quick_prompt_input = action["prompt"]


# ==========================================
# TAMPILAN RIWAYAT CHAT
# ==========================================
for msg in st.session_state.messages:
    if msg["role"] == "user":
        with st.chat_message("user", avatar="👤"):
            st.markdown(msg["content"])
    else:
        with st.chat_message("assistant", avatar=current_persona["avatar"]):
            st.markdown(msg["content"])


# ==========================================
# PENANGANAN INPUT PENGGUNA & RESPONSE
# ==========================================
user_prompt = st.chat_input("Tanyakan sesuatu pada AURA atau diskusikan agenda hari ini...")

# Prioritaskan prompt dari Quick Action jika diklik
if st.session_state.quick_prompt_input:
    user_prompt = st.session_state.quick_prompt_input
    st.session_state.quick_prompt_input = None

if user_prompt:
    # 1. Simpan pesan pengguna ke state dan render di layar
    st.session_state.messages.append({"role": "user", "content": user_prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_prompt)

    # 2. Susun Konteks Real-Time (Cuaca dan Tugas Terbuka)
    active_tasks = [t["task"] for t in st.session_state.tasks if not t["completed"]]
    tasks_summary = ", ".join(active_tasks) if active_tasks else "Semua tugas saat ini telah selesai!"
    weather_summary = st.session_state.weather_cache.get("summary", "Informasi cuaca tidak tersedia.")

    live_context = (
        f"- Cuaca: {weather_summary}\n"
        f"- Daftar Tugas yang Belum Selesai: {tasks_summary}"
    )

    # 3. Panggil Gemini Client
    client = GeminiAssistantClient(
        api_key=api_key_input,
        model_name=selected_model,
        temperature=temp_val
    )

    # 4. Stream respon AI
    with st.chat_message("assistant", avatar=current_persona["avatar"]):
        # History sliding window (10 turn terakhir)
        history = st.session_state.messages[:-1]
        response_generator = client.generate_chat_stream(
            prompt=user_prompt,
            system_instruction=current_persona["system_instruction"],
            history=history,
            live_context=live_context
        )
        full_response = st.write_stream(response_generator)

    # 5. Simpan respon ke state
    st.session_state.messages.append({"role": "model", "content": full_response})

# Footer informasi
st.markdown(
    '<div class="footer-note">AURA Assistant • Hacktiv8 Final Project: LLM-Based Tools & Gemini API Integration</div>',
    unsafe_allow_html=True
)
