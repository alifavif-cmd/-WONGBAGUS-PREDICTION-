import requests
import json
import time
import os
from bs4 import BeautifulSoup
import re
from datetime import datetime

OUTPUT_FILE = 'result.json'

# GUNAKAN URL YANG PALING STABIL & BISA DIAKSES
MARKETS = [
    {"name": "Hongkong Pools", "url": "https://angkanet18.com/paito-harian/"},
]

def fetch_html(url):
    headers = {'User-Agent': 'Mozilla/5.0'}
    try:
        response = requests.get(url, headers=headers, timeout=15)
        return response.text
    except:
        return None

def extract_result_and_rows(html_content):
    if not html_content: return None, []
    soup = BeautifulSoup(html_content, 'lxml')
    latest_result = None
    history = []
    
    # Cari per baris paito-line
    paito_lines = soup.find_all('div', class_='paito-line')
    
    for idx, line in enumerate(paito_lines):
        digits = line.find_all('span', class_='paito-digit')
        if digits:
            raw = ''.join([d.get_text(strip=True) for d in digits])
            clean = re.sub(r'[^0-9]', '', raw)
            if len(clean) >= 4:
                res = clean[:4]
                if idx == 0: latest_result = res
                else: 
                    if res not in history: history.append(res)
                    
    return latest_result, history[:20]

def main():
    all_data = {}
    for m in MARKETS:
        print(f"Processing {m['name']}...")
        html = fetch_html(m['url'])
        if html:
            latest, hist = extract_result_and_rows(html)
            if latest:
                print(f"Success: {latest}")
                all_data[m['name']] = {"latest_result": latest, "history": hist, "last_updated": str(datetime.now())}
            else:
                print("Failed to extract.")
        else:
            print("Failed to fetch HTML.")
            
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(all_data, f, indent=2)

if __name__ == "__main__":
    main()
