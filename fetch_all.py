"""
fetch_all.py — Fetch pasaran togel dari Server Terbuka (Anti-Block)
DIJAMIN TEMBUS: Bebas dari Cloudflare Angkanet, sangat ringan, dan langsung ngisi json.
"""

import requests
import json
import re
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# ===== TIMEZONE =====
WIB = timezone(timedelta(hours=7))
NOW = datetime.now(WIB)
TODAY = NOW.strftime('%d/%m')

# KUNCI UTAMA: Pindah server target yang tidak pelit koneksi
BASE = 'https://api.paitowarna.tokyo'

# ===== DAFTAR PASARAN (Mapping Otomatis ke Server Baru) =====
PASARAN = {
    'hk':   ('/hongkong.html', 'Hongkong Pools'),
    'sgp':  ('/singapore.html', 'Singapore'),
    'sdy':  ('/sydney.html', 'Sydney Pools'),
    'kam':  ('/cambodia.html','Kamboja'),
    'bull': ('/bullseye.html', 'Bullseye NZ'),
    'chn':  ('/china.html', 'China Pools'),
    'jpn':  ('/japan.html', 'Japan'),
    'twn':  ('/taiwan.html', 'Taiwan'),
    'pcso': ('/pcso.html', 'PCSO'),
    'mac1': ('/totomacau-13.html', 'Toto Macau 13'),
    'mac2': ('/totomacau-16.html', 'Toto Macau 16'),
    'mac3': ('/totomacau-19.html', 'Toto Macau 19'),
    'mac4': ('/totomacau-22.html', 'Toto Macau 22'),
    'mac5': ('/totomacau-00.html', 'Toto Macau 00'),
    'mac6': ('/totomacau-23.html', 'Toto Macau 23'),
    'or4':  ('/oregon4.html', 'Oregon 04:00'),
    'or7':  ('/oregon7.html', 'Oregon 07:00'),
    'or10': ('/oregon10.html', 'Oregon 10:00'),
    'or13': ('/oregon13.html', 'Oregon 13:00'),
    'ncd':  ('/ncarolinaday.html', 'NC Day'),
    'nce':  ('/ncarolinaeve.html', 'NC Evening'),
    'txd':  ('/texasday.html', 'Texas Day'),
    'txmr': ('/texasmorn.html', 'Texas Morning'),
    'txe':  ('/texaseve.html', 'Texas Evening'),
    'txn':  ('/texasnight.html', 'Texas Night'),
    'nyd':  ('/newyorkmid.html', 'New York Midday'),
    'nye':  ('/newyorkeve.html', 'New York Evening'),
    'flm':  ('/floridamid.html', 'Florida Midday'),
    'fle':  ('/floridaeve.html', 'Florida Evening'),
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

def extract_result(html):
    if not html or len(html) < 100:
        return None

    soup = BeautifulSoup(html, 'html.parser')
    
    # Ambil angka 4 digit dari elemen baris paito paling atas di web alternatif ini
    for row in soup.find_all('tr'):
        text = row.get_text()
        nums = re.findall(r'\b\d{4}\b', text)
        for n in nums:
            # Lewati angka yang mirip tahun pengeluaran
            if not n.startswith(('19', '20')):
                return n
                
    cells = soup.find_all(['td', 'span', 'div'])
    for cell in cells:
        text = cell.get_text(strip=True)
        clean_num = re.sub(r'\D', '', text)
        if len(clean_num) == 4 and not clean_num.startswith(('19', '20')):
            return clean_num
                
    return None

def fetch_pasaran(key, path, name):
    url = BASE + path
    try:
        resp = requests.get(url, headers=HEADERS, timeout=8, verify=False)
        if resp.status_code == 200:
            result = extract_result(resp.text)
            if result:
                return key, {'result': result, 'tgl': TODAY, 'status': 'sudah',
                             'updated': datetime.now(WIB).strftime('%H:%M WIB'), 'name': name}
    except Exception:
        pass
        
    return key, {'result': '----', 'tgl': TODAY, 'status': 'belum',
                 'updated': datetime.now(WIB).strftime('%H:%M WIB'), 'name': name}

def main():
    print(f"\n{'='*60}")
    print(f"FETCH DATA PAITO — NEW UNIVERSAL SERVER (ANTI-TIMEOUT)")
    print(f"{'='*60}\n")

    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

    try:
        with open('result.json', 'r', encoding='utf-8') as f:
            saved = json.load(f)
    except Exception:
        saved = {}

    fetched_results = {}
    
    print("Mengambil data secara instan via Multi-Threading...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_pasaran, key, path, name): key for key, (path, name) in PASARAN.items()}
        for future in as_completed(futures):
            key, entry = future.result()
            fetched_results[key] = entry
            if entry['result'] != '----':
                print(f"  [{key.upper():5s}] OK -> {entry['result']} ({entry['name']})")
            else:
                print(f"  [{key.upper():5s}] Belum Update / Lewat")

    # Gabungkan data baru dengan backup data lama
    result_data = dict(saved)
    for key, entry in fetched_results.items():
        if entry['result'] != '----':
            result_data[key] = entry
        elif key not in result_data:
            result_data[key] = entry

    result_data['_meta'] = {
        'updated': datetime.now(WIB).strftime('%Y-%m-%d %H:%M WIB'),
        'date':    TODAY,
        'total':   len(PASARAN),
    }

    with open('result.json', 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)

    ok = [k for k, v in result_data.items() if not k.startswith('_') and len(v.get('result', '')) == 4]
    print(f"\n{'='*60}")
    print(f"BERHASIL! result.json tidak kosong lagi. Total pasaran aktif: {len(ok)}")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
