import requests
import json
import time
import os
from bs4 import BeautifulSoup
import re
from datetime import datetime

# Konfigurasi
OUTPUT_FILE = 'result.json'

# Daftar pasaran (sesuaikan URL jika perlu)
MARKETS = [
    {"name": "Hongkong Pools", "url": "https://wong168.cc/paito-harian-hongkong/"},
    {"name": "Singapore Pools", "url": "https://wong168.cc/paito-harian-singapore/"},
    # Tambahkan pasaran lain di sini
]

def fetch_html(url):
    """Mengambil konten HTML dari URL."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_result_and_rows(html_content):
    """
    Fungsi perbaikan untuk ekstraksi data dari situs dengan class 'paito-digit'.
    """
    if not html_content:
        return None, []

    soup = BeautifulSoup(html_content, 'lxml')
    latest_result = None
    history = []

    try:
        # --- EKSTRAKSI HASIL TERBARU ---
        digit_spans = soup.find_all('span', class_='paito-digit')
        
        if digit_spans:
            raw_text = ''.join([span.get_text(strip=True) for span in digit_spans])
            clean_number = re.sub(r'[^0-9]', '', raw_text)
            if len(clean_number) >= 4:
                latest_result = clean_number[:4]

        # --- EKSTRAKSI RIWAYAT ---
        line_divs = soup.find_all('div', class_='paito-line')
        
        for line in line_divs:
            line_digits = line.find_all('span', class_='paito-digit')
            if line_digits:
                line_text = ''.join([d.get_text(strip=True) for d in line_digits])
                line_clean = re.sub(r'[^0-9]', '', line_text)
                if len(line_clean) == 4 and line_clean != latest_result:
                    if line_clean not in history:
                        history.append(line_clean)
                        
        history = history[:20]  # Batasi riwayat

    except Exception as e:
        print(f"Error during extraction: {e}")
        return None, []

    return latest_result, history

def load_existing_data():
    """Memuat data lama dari result.json jika ada."""
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_data(data):
    """Menyimpan data ke result.json."""
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    print(f"Data saved to {OUTPUT_FILE}")

def main():
    all_data = load_existing_data()
    
    for market in MARKETS:
        name = market['name']
        url = market['url']
        print(f"\nProcessing: {name}...")
        
        html = fetch_html(url)
        if html:
            latest, hist = extract_result_and_rows(html)
            
            if latest:
                print(f"   Success: Latest Result = {latest}")
                
                # Update struktur data
                if name not in all_data:
                    all_data[name] = {"latest_result": None, "history": [], "last_updated": ""}
                
                all_data[name]["latest_result"] = latest
                
                # Gabungkan history baru dengan lama (hindari duplikat)
                existing_hist = all_data[name].get("history", [])
                new_history = [h for h in hist if h not in existing_hist]
                all_data[name]["history"] = new_history + existing_hist
                all_data[name]["history"] = all_data[name]["history"][:20] # Batasi total history
                
                all_data[name]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                print(f"   Failed: Could not extract result for {name}")
        else:
            print(f"   Failed: Could not fetch HTML for {name}")
        
        time.sleep(2)  # Jeda antar request

    save_data(all_data)

if __name__ == "__main__":
    main()
