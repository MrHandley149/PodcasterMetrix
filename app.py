import requests
import csv
import time
from datetime import datetime, timedelta

# --- DINA INSTÄLLNINGAR ---
API_TOKEN = "Nyckel här" # Klistra in din nyckel här
DAGAR_BAKAT = 180 # Ändra till 90 eller 180 om du vill hämta mer historik första gången
PODCASTS = {
    664657: "Småbrukarpodden",
    2323408: "Lilla Surdegspodden"
}
# --------------------------

BASE_URL = "https://www.buzzsprout.com/api"
HEADERS = {
    "Authorization": f"Token token={API_TOKEN}",
    "User-Agent": "LilltorpMetricsCollector/1.0",
    "Accept": "application/json"
}

def hämta_avsnittsnamn():
    """Hämtar alla avsnitt för att kunna översätta ID till riktiga titlar i CSV-filen."""
    avsnitt_karta = {}
    print("Hämtar avsnittsregister...")
    for pod_id in PODCASTS.keys():
        response = requests.get(f"{BASE_URL}/{pod_id}/episodes", headers=HEADERS)
        if response.status_code == 200:
            for ep in response.json():
                avsnitt_karta[ep['id']] = ep['title']
    return avsnitt_karta

def samla_in_data():
    if API_TOKEN == "din_långa_nyckel_här":
        print("OBS! Glöm inte att lägga in din API-token högst upp i skriptet.")
        return

    avsnitt_karta = hämta_avsnittsnamn()
    alla_rader = []
    
    today = datetime.now()
    datumar_att_hämta = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(DAGAR_BAKAT)]
    
    print(f"Hämtar daglig statistik för de senaste {DAGAR_BAKAT} dagarna...\n")
    
    for pod_id, pod_namn in PODCASTS.items():
        print(f"Bearbetar {pod_namn}...")
        
        for datum in datumar_att_hämta:
            url = f"{BASE_URL}/{pod_id}/downloads?date={datum}"
            svar = requests.get(url, headers=HEADERS)
            
            if svar.status_code == 200:
                data = svar.json()
                for post in data:
                    ep_id = post.get('episode_id')
                    ep_titel = avsnitt_karta.get(ep_id, "Okänt avsnitt")
                    nedladdningar = post.get('total', 0)
                    
                    alla_rader.append([datum, pod_namn, ep_id, ep_titel, nedladdningar])
            elif svar.status_code == 429:
                print(f"Varning: Slog i taket för API-anrop på datum {datum}. Ökar paustiden.")
                time.sleep(10) # Vänta extra länge om vi blir blockade
            
            # Pausa drygt 1 sekund för att inte spräcka gränsen på 60 anrop/minut
            time.sleep(1.1)

    # Skriv till CSV
    filnamn = "buzzsprout_statistik.csv"
    print(f"\nSparar data till {filnamn}...")
    
    # encoding='utf-8-sig' gör att Excel i Windows läser in å, ä, ö automatiskt
    with open(filnamn, mode='w', newline='', encoding='utf-8-sig') as fil:
        writer = csv.writer(fil, delimiter=';')
        writer.writerow(["Datum", "Podd", "Avsnitts-ID", "Avsnittstitel", "Nedladdningar"])
        writer.writerows(alla_rader)
        
    print(f"Klar! {len(alla_rader)} rader med data har sparats.")

if __name__ == "__main__":
    samla_in_data()
