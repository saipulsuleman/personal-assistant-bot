"""
External Tools and Utilities for AURA Assistant
Includes:
1. Live Weather Integration (Open-Meteo API - Free, No API Key Required)
"""
import requests
from typing import Dict, Any

# Mapping WMO Weather Code ke Bahasa Indonesia & Emoji
WEATHER_CODE_MAP = {
    0: ("☀️ Cerah", "Langit sangat bersih dan cerah."),
    1: ("🌤️ Sebagian Besar Cerah", "Cuaca cukup bagus dengan sedikit awan."),
    2: ("⛅ Sebagian Berawan", "Kondisi berawan sedang, nyaman untuk bepergian."),
    3: ("☁️ Berawan Tebal", "Langit mendung tertutup awan."),
    45: ("🌫️ Berkabut", "Visibilitas berkurang akibat kabut tipis."),
    48: ("🌫️ Kabut Tebal", "Udara berkabut dingin."),
    51: ("🌦️ Gerimis Ringan", "Ada gerimis tipis, siapkan payung jika keluar."),
    53: ("🌦️ Gerimis Sedang", "Gerimis cukup terasa, waspadai jalan licin."),
    55: ("🌧️ Gerimis Lebat", "Hujan rintik cukup rapat."),
    61: ("🌧️ Hujan Ringan", "Hujan intensitas rendah, cocok kerja di dalam ruangan."),
    63: ("🌧️ Hujan Sedang", "Hujan merata, pastikan bawa jas hujan/payung."),
    65: ("⛈️ Hujan Lebat", "Hujan deras disertai angin, utamakan keselamatan."),
    80: ("🌧️ Hujan Lokal Singkat", "Hujan sesaat yang berpotensi turun tiba-tiba."),
    95: ("⛈️ Badai Petir", "Badai guntur, hindari aktivitas luar ruang.")
}


def get_live_weather(city_name: str = "Jakarta") -> Dict[str, Any]:
    """
    Mengambil data cuaca real-time menggunakan Open-Meteo API publik gratis.
    Tidak memerlukan API key pihak ketiga.
    """
    try:
        # Step 1: Geocoding (Mencari koordinat kota)
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_name.strip()}&count=1&language=id&format=json"
        geo_res = requests.get(geo_url, timeout=5)
        
        if geo_res.status_code != 200:
            return {"success": False, "message": f"Gagal menghubungi server geocoding ({geo_res.status_code})"}
        
        geo_data = geo_res.json()
        if "results" not in geo_data or len(geo_data["results"]) == 0:
            return {"success": False, "message": f"Kota '{city_name}' tidak ditemukan. Coba nama kota lain seperti Jakarta, Bandung, atau Surabaya."}
        
        location = geo_data["results"][0]
        lat = location["latitude"]
        lon = location["longitude"]
        resolved_name = location.get("name", city_name)
        country = location.get("country", "")
        
        # Step 2: Mengambil Cuaca Terkini
        weather_url = (
            f"https://api.open-meteo.com/v1/forecast?"
            f"latitude={lat}&longitude={lon}&current_weather=true"
        )
        weather_res = requests.get(weather_url, timeout=5)
        if weather_res.status_code != 200:
            return {"success": False, "message": f"Gagal mengambil cuaca ({weather_res.status_code})"}
        
        weather_data = weather_res.json()
        current = weather_data.get("current_weather", {})
        
        temp = current.get("temperature", "--")
        w_code = current.get("weathercode", 0)
        wind = current.get("windspeed", "--")
        
        condition_title, condition_desc = WEATHER_CODE_MAP.get(
            w_code, ("🌤️ Cuaca Sedang", "Kondisi cuaca normal.")
        )
        
        summary_text = (
            f"Kondisi cuaca saat ini di {resolved_name}, {country}: "
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
