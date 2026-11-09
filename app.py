import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import time

# --- Konfiguration ---
st.set_page_config(page_title="Podcaster Metrix", page_icon="📈", layout="centered")

PODCASTS = {
    664657: "Småbrukarpodden",
    2323408: "Lilla Surdegspodden"
}
BASE_URL = "https://www.buzzsprout.com/api"

# Skapar en textsträng av namnen i konstanten (t.ex. "Småbrukarpodden och Lilla Surdegspodden")
podd_namn = list(PODCASTS.values())
podd_str_sv = " och ".join(podd_namn)
podd_str_en = " and ".join(podd_namn)

# --- Språkhantering (Translations) ---
TRANSLATIONS = {
    "Svenska": {
        "desc": f"Dagsstatistik för {podd_str_sv}.",
        "api_input": "Mata in din Buzzsprout API-nyckel:",
        "days_slider": "Hur många dagar bakåt vill du titta?",
        "trend_slider": "Utjämning av trendkurva (dagar)",
        "btn_fetch": "Hämta statistik",
        "fetching": "Hämtar data från Buzzsprout...",
        "success": "Data hämtad!",
        "no_data": "Ingen aktivitet hittades för vald period.",
        "sub_daily": "Totala nedladdningar per dag",
        "unknown": "Okänt"
    },
    "English": {
        "desc": f"Daily statistics for {podd_str_en}.",
        "api_input": "Enter your Buzzsprout API key:",
        "days_slider": "How many days back do you want to look?",
        "trend_slider": "Trend curve smoothing (days)",
        "btn_fetch": "Fetch statistics",
        "fetching": "Fetching data from Buzzsprout...",
        "success": "Data fetched successfully!",
        "no_data": "No activity found for the selected period.",
        "sub_daily": "Total downloads per day",
        "unknown": "Unknown"
    }
}

# Sidofält för språkval
st.sidebar.title("Inställningar / Settings")
lang_choice = st.sidebar.radio("Språk / Language", ["Svenska", "English"])
t = TRANSLATIONS[lang_choice] # Laddar vald ordlista

# --- UI och Inloggning ---
st.title("🎙️ Podcaster Metrix")
st.write(t["desc"])

# Hämta API-nyckel från Streamlits inbyggda hemligheter (secrets)
try:
    API_TOKEN = st.secrets["BUZZSPROUT_API_TOKEN"]
