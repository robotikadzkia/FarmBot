# streamlit_app.py
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time
import google.generativeai as genai
import re

temperature_value = 0
humidity_value = 0      
kelembaban_tanah_value = 0
ldr_value = 0

URL_temperature = "https://stem.ubidots.com/api/v1.6/devices/esp32/suhu/lv"
URL_humidity = "https://stem.ubidots.com/api/v1.6/devices/esp32/kelembaban_udara/lv"
URL_kelembaban_tanah = "https://stem.ubidots.com/api/v1.6/devices/esp32/kelembaban_tanah/lv"
URL_ldr = "https://stem.ubidots.com/api/v1.6/devices/esp32/ldr/lv"

headers = {"X-Auth-Token": "BBUS-ZndsF354PFGLFNWiJFXLqV7qlsyh0g"}

# ========== KONFIGURASI ==========
st.set_page_config(
    page_title="FarmBot Genesis",
    layout="wide",
    page_icon="🏫"
)

# ========== GEMINI ENGINE ==========
class GeminiRecommendationEngine:
    def __init__(self):
        if 'GEMINI_API_KEY' not in st.secrets:
            st.error("API Key Gemini tidak ditemukan di secrets.toml")
            self.enabled = False
            return
        try:
            genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
            available_models = [m.name for m in genai.list_models()]
            self.model_name = "models/gemini-2.0-flash"# if "models/gemini-2.0-flash" in available_models else "models/gemini-pro"
            self.model = genai.GenerativeModel(self.model_name)
            self.enabled = True
        except Exception as e:
            st.error(f"Gagal inisialisasi Gemini: {str(e)}")
            self.enabled = False

    def generate_recommendations(self):
        if not self.enabled:
            return ["⚠️ Sistem rekomendasi AI tidak aktif"]

        try:
            prompt = f"""
            Buat 3 rekomendasi spesifik dan singkat untuk menganalisis kondisi lingkungan pertanian terhadap kesuburan tanah berdasarkan data berikut: 
            - Suhu Udara: {st.session_state.temperature} °C
            - Kelembaban Udara: {st.session_state.humidity} %
            - Cahaya: {st.session_state.ldr} Lux
            - Kelembaban Tanah: {st.session_state.kelembaban_tanah} %  
            Format markdown dengan heading dan bullet point.
            """
            response = self.model.generate_content(prompt)
            return self._parse_recommendations(response.text)
        except Exception as e:
            st.error(f"Error: {str(e)}")
            return ["⚠️ Tidak dapat menghasilkan rekomendasi"]

    def _parse_recommendations(self, text):
        parts = [s.strip() for s in text.split("###") if s.strip()]
        return parts[:3] if parts else ["⚠️ Tidak ada data yang bisa ditampilkan"]

# ========== DASHBOARD ==========
def main():
    st.title("🏫 FarmBot Genesis")
    engine = GeminiRecommendationEngine()

    if "temperature" not in st.session_state:
        st.session_state.temperature = 0
    if "humidity" not in st.session_state:
        st.session_state.humidity = 0   
    if "kelembaban_tanah" not in st.session_state:
        st.session_state.kelembaban_tanah = 0
    if "ldr" not in st.session_state:
        st.session_state.ldr = 0
    if "llm" not in st.session_state:   
        st.session_state.llm = ""

    response_temperature = requests.get(URL_temperature,headers=headers)
    response_humidity = requests.get(URL_humidity,headers=headers)
    response_kelembaban_tanah = requests.get(URL_kelembaban_tanah,headers=headers)
    response_ldr = requests.get(URL_ldr,headers=headers)

    temperature_value = response_temperature.text
    humidity_value = response_humidity.text
    kelembaban_tanah_value = response_kelembaban_tanah.text
    ldr_value = response_ldr.text    

    st.session_state.temperature = temperature_value
    st.session_state.humidity = humidity_value
    st.session_state.kelembaban_tanah = kelembaban_tanah_value
    st.session_state.ldr = ldr_value

    # st.session_state.temperature = 25.5
    # st.session_state.humidity = 85
    # st.session_state.kelembaban_tanah = 60
    # st.session_state.ldr = 3100

    col1,col2,col3,col4 = st.columns(4)
    col1.metric("🌡️ Sensor Suhu DHT22", f"{st.session_state.temperature} °C")
    col2.metric("💧 Kelembaban Udara DHT22", f"{st.session_state.humidity} %")  
    col3.metric("📡 Sensor kelembaban Tanah", f"{st.session_state.kelembaban_tanah} %")
    col4.metric("💡 Sensor LDR", f"{st.session_state.ldr} Lux")
    st.write(st.session_state.llm)  

    with st.sidebar:
        st.header("📊== INFORMASI SENSOR ==📊")
        st.markdown("### 🎯 Nilai Kondisi Normal")
        st.markdown("- 🌡️ Suhu Udara: 21–27 °C\n- 💧 Kelembaban Udara: 80–90 %\n- 📡 Kelembaban Tanah: 50-70 %\n- 💡 Cahaya: 3000–3300 Lux" )

    st.markdown("## 🧠 Rekomendasi AI")

    if st.button("✨ Hasilkan Rekomendasi AI"):
        with st.spinner("Menganalisis Kondisi Lingkungan..."):
            st.session_state.recommendations = engine.generate_recommendations()
            st.session_state.show_recommendations = True

    if st.session_state.get("show_recommendations", False):
        with st.expander("📋 Lihat Rekomendasi Lengkap", expanded=True):
            for rec in st.session_state.get("recommendations", []):
                st.markdown(f"### {rec.splitlines()[0]}")
                for line in rec.splitlines()[1:]:
                    st.markdown(line)

    # Auto-refresh
    # time.sleep(REFRESH_INTERVAL)
    # st.rerun()

# ========== RUN APLIKASI ==========
if __name__ == "__main__":
    main()