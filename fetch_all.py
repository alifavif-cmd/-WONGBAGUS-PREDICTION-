"""
fetch_all.py — Fetch 65 pasaran togel dari angkanet.com (159.65.133.131)
FIX RADIKAL: Custom SSL Session adapter untuk bypass "Max retries exceeded" 
dan pembacaan tabel akurat dari baris paling bawah.
"""

import requests
import json
import re
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

# ===== TIMEZONE =====
WIB = timezone(timedelta(hours=7))
NOW = datetime.now(WIB)
TODAY = NOW.strftime('%d/%m')

# Kembalikan ke HTTPS karena server mereka hanya merespon port 443
BASE = 'https://159.65.133.131'

# ===== DAFTAR 65 PASARAN =====
PASARAN = {
    'hk':   ('/data-pengeluaran-togel-hongkong-pools/', 'Hongkong Pools'),
    'hkl':  ('/data-pengeluaran-togel-hklotto/',        'Hongkong Lotto'),
    'sgp':  ('/data-pengeluaran-togel-singapore/',      'Singapore'),
    'sdy':  ('/data-pengeluaran-togel-sydney-pools/',   'Sydney Pools'),
    'sdl':  ('/data-pengeluaran-togel-sdlotto/',        'Sydney Lotto'),
    'kam':  ('/data-pengeluaran-togel-magnum-cambodia/','Kamboja'),
    'bull': ('/data-pengeluaran-togel-bullseye/',       'Bullseye NZ'),
    'chn':  ('/data-pengeluaran-togel-chinapools/',     'China Pools'),
    'jpn':  ('/data-pengeluaran-togel-japan/',          'Japan'),
    'twn':  ('/data-pengeluaran-togel-taiwan/',         'Taiwan'),
    'pcso': ('/data-pengeluaran-togel-pcso/',           'PCSO'),
    'mac':  ('/data-pengeluaran-togel-toto-macau-1/',   'Macau (alias)'),
    'mac1': ('/data-pengeluaran-togel-toto-macau-1/',   'Toto Macau 13'),
    'mac2': ('/data-pengeluaran-togel-toto-macau-2/',   'Toto Macau 16'),
    'mac3': ('/data-pengeluaran-togel-toto-macau-3/',   'Toto Macau 19'),
    'mac4': ('/data-pengeluaran-togel-toto-macau-4/',   'Toto Macau 22'),
    'mac5': ('/data-pengeluaran-togel-toto-macau-5/',   'Toto Macau 00'),
    'mac6': ('/data-pengeluaran-togel-toto-macau-6/',   'Toto Macau 23'),
    'mrq3':  ('/data-pengeluaran-togel-morocco-quatro-03-00-wib/', 'Morocco 03:00'),
    'mrq18': ('/data-pengeluaran-togel-morocco-quatro-18-00-wib/', 'Morocco 18:00'),
    'mrq21': ('/data-pengeluaran-togel-morocco-quatro-21-00-wib/', 'Morocco 21:00'),
    'mrq23': ('/data-pengeluaran-togel-morocco-quatro-23-59-wib/', 'Morocco 23:59'),
    'ger':  ('/data-pengeluaran-togel-germany-plus5/', 'Germany Plus5'),
    'or4':  ('/data-pengeluaran-togel-oregon-04-00-wib/', 'Oregon 04:00'),
    'or7':  ('/data-pengeluaran-togel-oregon-07-00-wib/', 'Oregon 07:00'),
    'or10': ('/data-pengeluaran-togel-oregon-10-00-wib/', 'Oregon 10:00'),
    'or13': ('/data-pengeluaran-togel-oregon-13-00-wib/', 'Oregon 13:00'),
    'ncd':  ('/data-pengeluaran-togel-north-carolina-day/',     'NC Day'),
    'nce':  ('/data-pengeluaran-togel-north-carolina-evening/', 'NC Evening'),
    'geom': ('/data-pengeluaran-togel-georgia-midday/',  'Georgia Midday'),
    'geoe': ('/data-pengeluaran-togel-georgia-evening/', 'Georgia Evening'),
    'geon': ('/data-pengeluaran-togel-georgia-night/',   'Georgia Night'),
    'txd':  ('/data-pengeluaran-togel-texas-day/',     'Texas Day'),
    'txmr': ('/data-pengeluaran-togel-texas-morning/', 'Texas Morning'),
    'txe':  ('/data-pengeluaran-togel-texas-evening/', 'Texas Evening'),
    'txn':  ('/data-pengeluaran-togel-texas-night/',   'Texas Night'),
    'nyd':  ('/data-pengeluaran-togel-new-york-midday/',  'New York Midday'),
    'nye':  ('/data-pengeluaran-togel-new-york-evening/', 'New York Evening'),
    'njm':  ('/data-pengeluaran-togel-new-jersey-midday/',  'NJ Midday'),
    'nje':  ('/data-pengeluaran-togel-new-jersey-evening/', 'NJ Evening'),
    'flm':  ('/data-pengeluaran-togel-florida-midday/',  'Florida Midday'),
    'fle':  ('/data-pengeluaran-togel-florida-evening/', 'Florida Evening'),
    'ilm':  ('/data-pengeluaran-togel-illinois-midday/',  'Illinois Midday'),
    'ile':  ('/data-pengeluaran-togel-illinois-evening/', 'Illinois Evening'),
    'indm': ('/data-pengeluaran-togel-indiana-midday/',  'Indiana Midday'),
    'inde': ('/data-pengeluaran-togel-indiana-evening/', 'Indiana Evening'),
    'kym':  ('/data-pengeluaran-togel-kentucky-midday/',  'Kentucky Midday'),
    'kye':  ('/data-pengeluaran-togel-kentucky-evening/', 'Kentucky Evening'),
    'mdm':  ('/data-pengeluaran-togel-maryland-midday/',  'Maryland Midday'),
    'mde':  ('/data-pengeluaran-togel-maryland-evening/', 'Maryland Evening'),
    'mim':  ('/data-pengeluaran-togel-michigan-midday/',  'Michigan Midday'),
    'mie':  ('/data-pengeluaran-togel-michigan-evening/', 'Michigan Evening'),
    'mom':  ('/data-pengeluaran-togel-missouri-midday/',  'Missouri Midday'),
    'moe':  ('/data-pengeluaran-togel-missouri-evening/', 'Missouri Evening'),
    'wdm':  ('/data-pengeluaran-togel-washington-dc-midday/',  'WDC Midday'),
    'wde':  ('/data-pengeluaran-togel-washington-dc-evening/', 'WDC Evening'),
    'ctd':  ('/data-pengeluaran-togel-connecticut-day/',   'Connecticut Day'),
    'ctn':  ('/data-pengeluaran-togel-connecticut-night/', 'Connecticut Night'),
    'vad':  ('/data-pengeluaran-togel-virginia-day/',   'Virginia Day'),
    'van':  ('/data-pengeluaran-togel-virginia-night/', 'Virginia Night'),
    'tnm':  ('/data-pengeluaran-togel-tennesse-midday/',  'Tennessee Midday'),
    'tne':  ('/data-pengeluaran-togel-tennesse-evening/', 'Tennessee Evening'),
    'tnmr': ('/data-pengeluaran-togel-tennesse-morning/', 'Tennessee Morning'),
    'cal':  ('/data-pengeluaran-togel-california/',        'California'),
    'wie':  ('/data-pengeluaran-togel-wisconsin-evening/', 'Wisconsin Evening'),
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'id,en-US;q=0.7,en;q=0.3',
}

# Membuat Session HTTP yang bandel (Anti-Drop)
def get_hardened_session():
    session = requests.Session()
    # Atur skema retry jika server sibuk / menolak koneksi sesaat
    retries = Retry(total=3, backoff_factor=0.5, status_forcelist=[500, 502, 503, 504])
    adapter = HTTPAdapter(max_retries=retries)
    session.mount('https://', adapter)
    session.mount('http://', adapter)
    return session

def extract_result(html):
    if not html or len(html) < 200:
        return None

    soup = BeautifulSoup(html, 'html.parser')
    tables = soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        if not rows:
            continue
            
        # BERDASARKAN MHTML: Data terbaru Angkanet diletakkan di baris PALING BAWAH
        # Kita baca terbalik menggunakan reversed() dari bawah ke atas
        for row in reversed(rows):
            cells = row.find_all(['td', 'th'])
            cols = [c.get_text(strip=True) for c in cells]
            
            if not cols or any(x in cols[0].lower() for x in ['hari', 'day', 'no', 'paito', 'total']):
                continue
                
            # Ambil angka 4 digit murni di dalam baris tersebut
            for cell_text in cols:
                clean_num = re.sub(r'\D', '', cell_text)
                # Validasi: Angka harus tepat 4 digit dan bukan tahun 202x
                if len(clean_num) == 4 and not clean_num.startswith(('19', '20')):
                    return clean_num

    return None

# Session global untuk menghemat proses handshake SSL
SESSION = get_hardened_session()

def fetch_pasaran(key, path, name):
    url = BASE + path
    try:
        # verify=False wajib dibarengi session terisolasi agar aman dari Max Retries
        resp = SESSION.get(url, headers=HEADERS, timeout=10, verify=False)
        resp.raise_for_status()
        result = extract_result(resp.text)
        if result:
            return key, {'result': result, 'tgl': TODAY, 'status': 'sudah',
                         'updated': datetime.now(WIB).strftime('%H:%M WIB'), 'name': name}
    except Exception as e:
        # Cetak error singkat jika ada timeout/gangguan jaringan di pasaran tertentu
        err_msg = str(e).split(']')[-1] if ']' in str(e) else str(e)[:30]
        print(f"  [{key.upper():6s}] Gagal: {err_msg}")
        
    return key, {'result': '----', 'tgl': TODAY, 'status': 'belum',
                 'updated': datetime.now(WIB).strftime('%H:%M WIB'), 'name': name}

def main():
    print(f"\n{'='*60}")
    print(f"FETCH DATA PAITO ANGKANET — {NOW.strftime('%A, %d %B %Y %H:%M WIB')}")
    print(f"{'='*60}\n")

    # Matikan log warning SSL dari urllib3 ke konsol
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

    try:
        with open('result.json', 'r', encoding='utf-8') as f:
            saved = json.load(f)
        print(f"Berhasil memuat {len([k for k in saved if not k.startswith('_')])} data lama.\n")
    except Exception:
        saved = {}

    fetched_results = {}
    
    print("Memulai proses unduh paito paralel (Max 10 Workers)...")
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(fetch_pasaran, key, path, name): key for key, (path, name) in PASARAN.items()}
        for future in as_completed(futures):
            key, entry = future.result()
            fetched_results[key] = entry
            if entry['result'] != '----':
                print(f"  [{key.upper():6s}] BERHASIL -> {entry['result']} ({entry['name']})")
            else:
                print(f"  [{key.upper():6s}] Skip / Belum Update")

    # Satukan data lama & baru
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
    print(f"SELESAI! result.json sukses ditulis. Total valid saat ini: {len(ok)} pasaran.")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
