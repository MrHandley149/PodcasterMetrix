import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import time

# --- Konfiguration ---
st.set_page_config(page_title="Lilltorp Podd-Metrik", page_icon="📈", layout="centered")

PODCASTS = {
    664657: "Småbrukarpodden",
    2323408: "Lilla Surdegspodden"
}
BASE_URL = "https://www.buzzsprout.com/api"

# --- UI och Inloggning ---
st.title("🎙️ Lilltorp Podd-Metrik")
st.write("Dagsstatistik för Småbrukarpodden och Lilla Surdegspodden.")

# Hämta API-nyckel från Streamlits inbyggda hemligheter (secrets)
try:
    API_TOKEN = st.secrets["BUZZSPROUT_API_TOKEN"]
except:
    API_TOKEN = st.text_input("Mata in din Buzzsprout API-nyckel:", type="password")

dagar_bakat = st.slider("Hur många dagar bakåt vill du titta?", min_value=7, max_value=90, value=30)

# --- Funktioner ---
@st.cache_data(ttl=3600) # Cachas i 1 timme så du inte slår i API-taket i onödan
def hamta_data(api_token, dagar):
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
                        "Avsnitt": avsnitt_karta.get(post.get('episode_id'), "Okänt"),
                        "Nedladdningar": post.get('total', 0)
                    })
            
            aktuellt_anrop += 1
            progress_bar.progress(aktuellt_anrop / total_anrop)
            time.sleep(1.1) # Respektera Buzzsprouts 60 req/min
            
    progress_bar.empty()
    return pd.DataFrame(rader)

# --- Exekvering och Grafer ---
if API_TOKEN and st.button("Hämta statistik"):
    with st.spinner("Hämtar data från Buzzsprout..."):
        df = hamta_data(API_TOKEN, dagar_bakat)
        
    if not df.empty:
        st.success("Data hämtad!")
        
        # Flikar för att skilja poddarna åt i mobilen
        tab1, tab2 = st.tabs(["Småbrukarpodden", "Lilla Surdegspodden"])
        
        with tab1:
            df_smabruk = df[df["Podd"] == "Småbrukarpodden"]
            st.subheader("Totala nedladdningar per dag")
            # Aggregera per dag och rita graf
            daglig_trend = df_smabruk.groupby("Datum")["Nedladdningar"].sum().reset_index()
            st.line_chart(daglig_trend.set_index("Datum"))
            st.dataframe(df_smabruk.sort_values("Datum", ascending=False), use_container_width=True)
            
        with tab2:
            df_surdeg = df[df["Podd"] == "Lilla Surdegspodden"]
            st.subheader("Totala nedladdningar per dag")
            daglig_trend = df_surdeg.groupby("Datum")["Nedladdningar"].sum().reset_index()
            st.line_chart(daglig_trend.set_index("Datum"))
            st.dataframe(df_surdeg.sort_values("Datum", ascending=False), use_container_width=True)
    else:
        st.warning("Ingen aktivitet hittades för vald period.")
