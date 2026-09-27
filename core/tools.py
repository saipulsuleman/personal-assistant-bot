"""
External Tools and Utilities for AURA Assistant
Includes:
1. Global Live Weather Integration (Open-Meteo API - Free, No API Key, Global Coverage)
2. Intelligent City Extractor for on-demand global weather lookup from chat
"""
import re
import requests
from typing import Dict, Any, Optional

# Mapping WMO Weather Code ke Bahasa Indonesia & Emoji
WEATHER_CODE_MAP = {
    0: ("☀️ Cerah", "Langit sangat bersih dan cerah."),
    1: ("🌤️ Sebagian Besar Cerah", "Cuaca cukup bagus dengan sedikit awan."),
    2: ("⛅ Sebagian Berawan", "Kondisi berawan sedang, nyaman untuk beraktivitas."),
    3: ("☁️ Berawan Tebal", "Langit mendung tertutup awan."),
    45: ("🌫️ Berkabut", "Visibilitas berkurang akibat kabut tipis."),
    48: ("🌫️ Kabut Tebal", "Udara berkabut tebal."),
    51: ("🌦️ Gerimis Ringan", "Ada gerimis tipis, siapkan payung jika keluar."),
    53: ("🌦️ Gerimis Sedang", "Gerimis cukup terasa, waspadai jalan licin."),
    55: ("🌧️ Gerimis Lebat", "Hujan rintik cukup rapat."),
    61: ("🌧️ Hujan Ringan", "Hujan intensitas rendah, cocok kerja di dalam ruangan."),
    63: ("🌧️ Hujan Sedang", "Hujan merata, pastikan bawa payung atau jas hujan."),
    65: ("⛈️ Hujan Lebat", "Hujan deras disertai angin, utamakan keselamatan."),
    80: ("🌧️ Hujan Lokal Singkat", "Hujan sesaat yang berpotensi turun tiba-tiba."),
    95: ("⛈️ Badai Petir", "Badai guntur, hindari aktivitas luar ruang.")
}

WEATHER_KEYWORDS = [
    "cuaca", "suhu", "temperature", "weather", "hujan", "panas", "dingin",
    "derajat", "celcius", "celsius", "iklim", "angin", "mendung", "cerah", "berawan"
]

STOPWORDS_CITY = {
    "hujan", "cerah", "panas", "dingin", "mendung", "berawan", "sejuk",
    "hari", "ini", "sekarang", "saat", "bagaimana", "gimana", "apakah",
    "besok", "lusa", "suhu", "cuaca", "kira", "sedang", "ada", "di", "kota",
    "wilayah", "daerah", "negara", "berapa", "derajat", "ya", "sih", "dong"
}


def get_live_weather(city_name: str = "Jakarta") -> Dict[str, Any]:
    """
    Mengambil data cuaca real-time untuk SELURUH KOTA DI DUNIA menggunakan Open-Meteo API.
    Mendukung kota domestik (Gorontalo, Bandung, Surabaya, dll.) maupun internasional (Tokyo, London, Paris, New York, dll.).
    """
    if not city_name or not city_name.strip():
        city_name = "Jakarta"

    clean_city = city_name.strip()

    try:
        # Step 1: Geocoding Global (Mencari koordinat kota di seluruh dunia)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={clean_city}&count=5&format=json"
        geo_res = requests.get(geo_url, timeout=5)

        if geo_res.status_code != 200:
            return {"success": False, "message": f"Gagal menghubungi server geocoding ({geo_res.status_code})"}

        geo_data = geo_res.json()
        if "results" not in geo_data or len(geo_data["results"]) == 0:
            return {"success": False, "message": f"Kota '{clean_city}' tidak ditemukan di database global."}

        # Pilih hasil paling relevan (prioritas utama)
        location = geo_data["results"][0]
        lat = location["latitude"]
        lon = location["longitude"]
        resolved_name = location.get("name", clean_city)
        country = location.get("country", "")

        # Step 2: Mengambil Cuaca Terkini dari Stasiun Meteorologi Global
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&current_weather=true"
        )
        weather_res = requests.get(weather_url, timeout=5)
        if weather_res.status_code != 200:
            return {"success": False, "message": f"Gagal mengambil data telemetri cuaca ({weather_res.status_code})"}

        weather_data = weather_res.json()
        current = weather_data.get("current_weather", {})

        temp = current.get("temperature", "--")
        w_code = current.get("weathercode", 0)
        wind = current.get("windspeed", "--")

        condition_title, condition_desc = WEATHER_CODE_MAP.get(
            w_code, ("🌤️ Cuaca Normal", "Kondisi cuaca tipikal.")
        )

        country_str = f", {country}" if country else ""
        summary_text = (
            f"Telemetri cuaca real-time saat ini di {resolved_name}{country_str}: "
            f"{condition_title}, Suhu {temp}°C, Kecepatan Angin {wind} km/h. {condition_desc}"
        )

        return {
            "success": True,
            "city": resolved_name,
            "country": country,
            "temperature": temp,
            "condition": condition_title,
            "description": condition_desc,
            "wind_speed": wind,
            "summary": summary_text
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"Koneksi cuaca gagal: {str(e)}"
        }


def extract_city_from_prompt(prompt: str) -> Optional[str]:
    """
    Mengekstrak nama kota dari prompt percakapan bahasa alami pengguna.
    Contoh: 'suhu saat ini di gorontalo' -> 'gorontalo'
            'cuaca di tokyo bagaimana' -> 'tokyo'
            'apakah bandung hujan' -> 'bandung'
    """
    text = prompt.strip()
    
    # 1. Coba pola eksplisit: "di <nama_kota>" atau "kota <nama_kota>"
    patterns = [
        r'\b(?:di|ke|kota|wilayah|daerah)\s+([a-zA-Z\s]{2,30})',
        r'\b(?:cuaca|suhu|weather|temperature)\s+(?:di\s+|kota\s+)?([a-zA-Z\s]{2,30})',
        r'([a-zA-Z\s]{2,30})\s+(?:cuaca|suhu|hujan)'
    ]
    
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            raw_candidate = m.group(1).strip()
            # Bersihkan dari kata-kata penanya / cuaca
            words = [
                w for w in re.findall(r'[a-zA-Z]+', raw_candidate)
                if w.lower() not in STOPWORDS_CITY
            ]
            if words:
                candidate = " ".join(words)
                # Validasi dengan geocoding cepat
                geo_check = requests.get(
                    f"https://geocoding-api.open-meteo.com/v1/search?name={candidate}&count=1&format=json",
                    timeout=3
                )
                if geo_check.status_code == 200:
                    data = geo_check.json()
                    if "results" in data and len(data["results"]) > 0:
                        return candidate
    return None


def resolve_live_weather_for_query(prompt: str, fallback_city: str = "Jakarta") -> Dict[str, Any]:
    """
    Secara dinamis mendeteksi kota yang ditanyakan di dalam chat.
    Jika ada kota spesifik (misal Gorontalo / Tokyo), ambil cuaca kota tersebut.
    Jika tidak ada kota spesifik, gunakan cuaca kota fallback dari sidebar.
    """
    is_weather_related = any(kw in prompt.lower() for kw in WEATHER_KEYWORDS)
    
    if is_weather_related:
        detected_city = extract_city_from_prompt(prompt)
        if detected_city:
            weather_result = get_live_weather(detected_city)
            if weather_result.get("success"):
                return weather_result

    # Default fallback
    return get_live_weather(fallback_city)
