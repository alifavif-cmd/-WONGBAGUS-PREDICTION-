import requests
import json
import time
import os
from bs4 import BeautifulSoup
import re
from datetime import datetime

# Konfigurasi
OUTPUT_FILE = 'result.json'

# Daftar Pasaran - GANTI DENGAN SITUS YANG BISA DIAKSES
MARKETS = [
    {"name": "Hongkong Pools", "url": "https://angkanet18.com/paito-harian/"},
    {"name": "Singapore Pools", "url": "https://angkanet18.com/paito-harian/"},  # Sesuaikan jika ada URL khusus SG
]

def fetch_html(url):
    """Mengambil konten HTML dari URL."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

def extract_result_and_rows(html_content):
    """
    Fungsi ekstraksi data yang DISUAIKAN dengan struktur HTML:
    <div class="paito-line"> -> <span class="paito-row-item"> -> <span class="paito-digit">
    """
    if not html_content:
        return None, []

    soup = BeautifulSoup(html_content, 'lxml')
    latest_result = None
    history = []

    try:
        # 1. Cari semua container baris hasil (paito-line)
        paito_lines = soup.find_all('div', class_='paito-line')
        
        if not paito_lines:
            # Fallback jika class berubah, coba cari semua span digit global
            all_digits = soup.find_all('span', class_='paito-digit')
            if all_digits:
                raw = ''.join([d.get_text(strip=True) for d in all_digits])
                clean = re.sub(r'[^0-9]', '', raw)
                if len(clean) >= 4:
                    latest_result = clean[:4]
            return latest_result, []

        # 2. Loop setiap baris untuk mengambil angka
        for idx, line in enumerate(paito_lines):
            digits = line.find_all('span', class_='paito-digit')
            
            if digits:
                raw_text = ''.join([d.get_text(strip=True) for d in digits])
                clean_number = re.sub(r'[^0-9]', '', raw_text)
                
                if len(clean_number) >= 4:
                    result_4d = clean_number[:4]
                    
                    if idx == 0:
                        latest_result = result_4d
                    else:
                        if result_4d not in history:
                            history.append(result_4d)
                            
        history = history[:20]

    except Exception as e:
        print(f"Error during extraction: {e}")
        return None, []

    return latest_result, history

def load_existing_data():
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            pass
    return {}

def save_data(data):
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
                print(f"   ✅ Success: Latest Result = {latest}")
                
                if name not in all_data:
                    all_data[name] = {"latest_result": None, "history": [], "last_updated": ""}
                
                all_data[name]["latest_result"] = latest
                
                existing_hist = all_data[name].get("history", [])
                combined_hist = hist + existing_hist
                seen = set()
                unique_hist = []
                for item in combined_hist:
                    if item not in seen:
                        seen.add(item)
                        unique_hist.append(item)
                
                all_data[name]["history"] = unique_hist[:20]
                all_data[name]["last_updated"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            else:
                print(f"   ❌ Failed: Could not extract result for {name}. Check HTML structure.")
        else:
            print(f"   ❌ Failed: Could not fetch HTML for {name} (Network/DNS Error)")
        
        time.sleep(3)

    save_data(all_data)

if __name__ == "__main__":
    main()
