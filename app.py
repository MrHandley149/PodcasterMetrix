import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import time

# --- Konfiguration ---
st.set_page_config(page_title="Podcaster Social Media Metrix", page_icon="📈", layout="centered")

PODCASTS = {
    664657: "Småbrukarpodden",
    2323408: "Lilla Surdegspodden"
}
BASE_URL = "https://www.buzzsprout.com/api"

# --- Språkhantering (Translations) ---
TRANSLATIONS = {
    "Svenska": {
        "desc": "Dagsstatistik för Småbrukarpodden och Lilla Surdegspodden.",
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
        "desc": "Daily statistics for Småbrukarpodden and Lilla Surdegspodden.",
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
except:
    API_TOKEN = st.text_input(t["api_input"], type="password")

dagar_bakat = st.slider(t["days_slider"], min_value=7, max_value=90, value=30)
trend_window = st.slider(t["trend_slider"], min_value=1, max_value=30, value=7)

# --- Funktioner ---
@st.cache_data(ttl=3600)
def hamta_data(api_token, dagar, lang_unknown):
    headers = {
        "Authorization": f"Token token={api_token}",
        "User-Agent": "LilltorpMetricsWeb/1.0",
        "Accept": "application/json"
    }
    
    # 1. Hämta avsnittsnamn
    avsnitt_karta = {}
    for pod_id in PODCASTS.keys():
        resp = requests.get(f"{BASE_URL}/{pod_id}/episodes", headers=headers)
        if resp.status_code == 200:
            for ep in resp.json():
                avsnitt_karta[ep['id']] = ep['title']
                
    # 2. Hämta dagsstatistik
    rader = []
    today = datetime.now()
    datumar = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(dagar)]
    
    progress_bar = st.progress(0)
    total_anrop = len(PODCASTS) * len(datumar)
    aktuellt_anrop = 0
    
    for pod_id, pod_namn in PODCASTS.items():
        for datum in datumar:
            url = f"{BASE_URL}/{pod_id}/downloads?date={datum}"
            svar = requests.get(url, headers=headers)
            
            if svar.status_code == 200:
                for post in svar.json():
                    rader.append({
                        "Datum": pd.to_datetime(datum),
                        "Podd": pod_namn,
                        "Avsnitt": avsnitt_karta.get(post.get('episode_id'), lang_unknown),
                        "Nedladdningar": post.get('total', 0)
                    })
            
            aktuellt_anrop += 1
            progress_bar.progress(aktuellt_anrop / total_anrop)
            time.sleep(1.1) 
            
    progress_bar.empty()
    return pd.DataFrame(rader)

# --- Exekvering och Grafer ---
if API_TOKEN and st.button(t["btn_fetch"]):
    with st.spinner(t["fetching"]):
        # Skickar med 'Okänt'/'Unknown' till funktionen
        df = hamta_data(API_TOKEN, dagar_bakat, t["unknown"])
        
    if not df.empty:
        st.success(t["success"])
        
        # Flikar för att skilja poddarna åt i mobilen
        tab1, tab2 = st.tabs(["Småbrukarpodden", "Lilla Surdegspodden"])
        
        with tab1:
            df_smabruk = df[df["Podd"] == "Småbrukarpodden"]
            st.subheader(t["sub_daily"])
            
            # Aggregera per dag och rita graf med trend
            daglig_trend1 = df_smabruk.groupby("Datum")["Nedladdningar"].sum().reset_index()
            if not daglig_trend1.empty:
                daglig_trend1.set_index("Datum", inplace=True)
                daglig_trend1['Trend'] = daglig_trend1['Nedladdningar'].rolling(window=trend_window, min_periods=1).mean()
                st.line_chart(daglig_trend1[['Nedladdningar', 'Trend']])
            
            st.dataframe(df_smabruk.sort_values("Datum", ascending=False), use_container_width=True)
            
        with tab2:
            df_surdeg = df[df["Podd"] == "Lilla Surdegspodden"]
            st.subheader(t["sub_daily"])
            
            # Aggregera per dag och rita graf med trend
            daglig_trend2 = df_surdeg.groupby("Datum")["Nedladdningar"].sum().reset_index()
            if not daglig_trend2.empty:
                daglig_trend2.set_index("Datum", inplace=True)
                daglig_trend2['Trend'] = daglig_trend2['Nedladdningar'].rolling(window=trend_window, min_periods=1).mean()
                st.line_chart(daglig_trend2[['Nedladdningar', 'Trend']])
            
            st.dataframe(df_surdeg.sort_values("Datum", ascending=False), use_container_width=True)
    else:
        st.warning(t["no_data"])
