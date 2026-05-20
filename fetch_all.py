"""
fetch_all.py — Fetch 65 pasaran togel dari angkanet.com (159.65.133.131)
Simpan ke result.json, dibaca langsung oleh index.html
"""

import requests
import json
import re
import time
import urllib3
urllib3.disable_warnings()
from collections import Counter
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

# ===== TIMEZONE =====
WIB = timezone(timedelta(hours=7))
NOW = datetime.now(WIB)
TODAY = NOW.strftime('%d/%m')

BASE = 'https://angkanet18.com'

# ===== DAFTAR 65 PASARAN =====
# Format: 'key': ('slug-path', 'Nama Display')
PASARAN = {
    # === ASIA UTAMA ===
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
    # === TOTO MACAU (6 sesi) ===
    'mac':  ('/data-pengeluaran-togel-toto-macau-1/',   'Macau (alias)'),  # backward-compat
    'mac1': ('/data-pengeluaran-togel-toto-macau-1/',   'Toto Macau 13'),
    'mac2': ('/data-pengeluaran-togel-toto-macau-2/',   'Toto Macau 16'),
    'mac3': ('/data-pengeluaran-togel-toto-macau-3/',   'Toto Macau 19'),
    'mac4': ('/data-pengeluaran-togel-toto-macau-4/',   'Toto Macau 22'),
    'mac5': ('/data-pengeluaran-togel-toto-macau-5/',   'Toto Macau 00'),
    'mac6': ('/data-pengeluaran-togel-toto-macau-6/',   'Toto Macau 23'),
    # === MOROCCO QUATRO (4 sesi) ===
    'mrq3':  ('/data-pengeluaran-togel-morocco-quatro-03-00-wib/', 'Morocco 03:00'),
    'mrq18': ('/data-pengeluaran-togel-morocco-quatro-18-00-wib/', 'Morocco 18:00'),
    'mrq21': ('/data-pengeluaran-togel-morocco-quatro-21-00-wib/', 'Morocco 21:00'),
    'mrq23': ('/data-pengeluaran-togel-morocco-quatro-23-59-wib/', 'Morocco 23:59'),
    # === GERMANY ===
    'ger':  ('/data-pengeluaran-togel-germany-plus5/', 'Germany Plus5'),
    # === OREGON (4 sesi) ===
    'or4':  ('/data-pengeluaran-togel-oregon-04-00-wib/', 'Oregon 04:00'),
    'or7':  ('/data-pengeluaran-togel-oregon-07-00-wib/', 'Oregon 07:00'),
    'or10': ('/data-pengeluaran-togel-oregon-10-00-wib/', 'Oregon 10:00'),
    'or13': ('/data-pengeluaran-togel-oregon-13-00-wib/', 'Oregon 13:00'),
    # === NORTH CAROLINA ===
    'ncd':  ('/data-pengeluaran-togel-north-carolina-day/',     'NC Day'),
    'nce':  ('/data-pengeluaran-togel-north-carolina-evening/', 'NC Evening'),
    # === GEORGIA ===
    'geom': ('/data-pengeluaran-togel-georgia-midday/',  'Georgia Midday'),
    'geoe': ('/data-pengeluaran-togel-georgia-evening/', 'Georgia Evening'),
    'geon': ('/data-pengeluaran-togel-georgia-night/',   'Georgia Night'),
    # === TEXAS ===
    'txd':  ('/data-pengeluaran-togel-texas-day/',     'Texas Day'),
    'txmr': ('/data-pengeluaran-togel-texas-morning/', 'Texas Morning'),
    'txe':  ('/data-pengeluaran-togel-texas-evening/', 'Texas Evening'),
    'txn':  ('/data-pengeluaran-togel-texas-night/',   'Texas Night'),
    # === NEW YORK ===
    'nyd':  ('/data-pengeluaran-togel-new-york-midday/',  'New York Midday'),
    'nye':  ('/data-pengeluaran-togel-new-york-evening/', 'New York Evening'),
    # === NEW JERSEY ===
    'njm':  ('/data-pengeluaran-togel-new-jersey-midday/',  'NJ Midday'),
    'nje':  ('/data-pengeluaran-togel-new-jersey-evening/', 'NJ Evening'),
    # === FLORIDA ===
    'flm':  ('/data-pengeluaran-togel-florida-midday/',  'Florida Midday'),
    'fle':  ('/data-pengeluaran-togel-florida-evening/', 'Florida Evening'),
    # === ILLINOIS ===
    'ilm':  ('/data-pengeluaran-togel-illinois-midday/',  'Illinois Midday'),
    'ile':  ('/data-pengeluaran-togel-illinois-evening/', 'Illinois Evening'),
    # === INDIANA ===
    'indm': ('/data-pengeluaran-togel-indiana-midday/',  'Indiana Midday'),
    'inde': ('/data-pengeluaran-togel-indiana-evening/', 'Indiana Evening'),
    # === KENTUCKY ===
    'kym':  ('/data-pengeluaran-togel-kentucky-midday/',  'Kentucky Midday'),
    'kye':  ('/data-pengeluaran-togel-kentucky-evening/', 'Kentucky Evening'),
    # === MARYLAND ===
    'mdm':  ('/data-pengeluaran-togel-maryland-midday/',  'Maryland Midday'),
    'mde':  ('/data-pengeluaran-togel-maryland-evening/', 'Maryland Evening'),
    # === MICHIGAN ===
    'mim':  ('/data-pengeluaran-togel-michigan-midday/',  'Michigan Midday'),
    'mie':  ('/data-pengeluaran-togel-michigan-evening/', 'Michigan Evening'),
    # === MISSOURI ===
    'mom':  ('/data-pengeluaran-togel-missouri-midday/',  'Missouri Midday'),
    'moe':  ('/data-pengeluaran-togel-missouri-evening/', 'Missouri Evening'),
    # === WASHINGTON DC ===
    'wdm':  ('/data-pengeluaran-togel-washington-dc-midday/',  'WDC Midday'),
    'wde':  ('/data-pengeluaran-togel-washington-dc-evening/', 'WDC Evening'),
    # === CONNECTICUT ===
    'ctd':  ('/data-pengeluaran-togel-connecticut-day/',   'Connecticut Day'),
    'ctn':  ('/data-pengeluaran-togel-connecticut-night/', 'Connecticut Night'),
    # === VIRGINIA ===
    'vad':  ('/data-pengeluaran-togel-virginia-day/',   'Virginia Day'),
    'van':  ('/data-pengeluaran-togel-virginia-night/', 'Virginia Night'),
    # === TENNESSEE ===
    'tnm':  ('/data-pengeluaran-togel-tennesse-midday/',  'Tennessee Midday'),
    'tne':  ('/data-pengeluaran-togel-tennesse-evening/', 'Tennessee Evening'),
    'tnmr': ('/data-pengeluaran-togel-tennesse-morning/', 'Tennessee Morning'),
    # === CALIFORNIA, WISCONSIN ===
    'cal':  ('/data-pengeluaran-togel-california/',        'California'),
    'wie':  ('/data-pengeluaran-togel-wisconsin-evening/', 'Wisconsin Evening'),
}

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8',
}

# ===== DETEKSI DATA PALSU =====
FAKE_PATTERNS = [
    r'^1234$', r'^2345$', r'^3456$', r'^4567$', r'^5678$',
    r'^6789$', r'^7890$', r'^8901$', r'^9012$', r'^0123$',
    r'^(\d)\1{3}$',
]

# Rentang angka yang termasuk TAHUN (bukan result togel)
def is_year(result):
    try:
        n = int(result)
        return 1800 <= n <= 2099  # semua angka yg terlihat seperti tahun
    except Exception:
        return False

def is_fake(result):
    if not result or not re.match(r'^\d{4}$', result):
        return True
    if is_year(result):
        return True
    return any(re.match(p, result) for p in FAKE_PATTERNS)


# ===== EKSTRAK RESULT DARI HTML =====
def extract_result(html):
    """
    Angkanet: <span class="paito-row-item">XXXX</span>
    Masalah: sidebar juga pakai class yang sama.
    Solusi: cari PARENT yang punya paito-row-item TERBANYAK = tabel utama.
    Item pertama di tabel utama = result terbaru.
    """
    if not html or len(html) < 200:
        return None

    soup = BeautifulSoup(html, 'html.parser')

    # Kumpulkan semua elemen paito-row-item
    all_items = soup.find_all(class_='paito-row-item')
    if not all_items:
        # Fallback: <span> atau <td> pertama yang isi tepat 4 digit valid
        for tag in ['span', 'td']:
            for el in soup.find_all(tag):
                t = el.get_text(strip=True)
                if re.match(r'^\d{4}$', t) and not is_fake(t):
                    return t
        return None

    # Cari parent yang punya paito-row-item TERBANYAK = tabel utama pasaran
    parent_counts = {}
    for item in all_items:
        p = item.parent
        pid = id(p)
        if pid not in parent_counts:
            parent_counts[pid] = {'el': p, 'count': 0, 'items': []}
        parent_counts[pid]['count'] += 1
        parent_counts[pid]['items'].append(item)

    # Ambil parent dengan item terbanyak
    best = max(parent_counts.values(), key=lambda x: x['count'])
    
    # Ambil item PERTAMA dari parent terbanyak = result terbaru
    for item in best['items']:
        t = item.get_text(strip=True)
        if re.match(r'^\d{4}$', t) and not is_fake(t):
            return t

    return None


# ===== FETCH SATU PASARAN =====
def fetch_pasaran(key, path, name):
    url = BASE + path
    try:
        time.sleep(0.5)  # delay 0.5s antar request hindari rate limit
        resp = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        resp.raise_for_status()
        result = extract_result(resp.text)
        if result:
            print(f"  [{key.upper():6s}] OK {result}  ({name})")
            return {'result': result, 'tgl': TODAY, 'status': 'sudah',
                    'updated': NOW.strftime('%H:%M WIB'), 'name': name}
        else:
            print(f"  [{key.upper():6s}] WARN angka tidak ketemu  ({name})")
    except requests.RequestException as e:
        print(f"  [{key.upper():6s}] ERR {e}  ({name})")
    except Exception as e:
        print(f"  [{key.upper():6s}] ERR {e}  ({name})")

    return {'result': '----', 'tgl': TODAY, 'status': 'belum',
            'updated': NOW.strftime('%H:%M WIB'), 'name': name}


# ===== MAIN =====
def main():
    print(f"\n{'='*60}")
    print(f"fetch_all.py — {NOW.strftime('%A, %d %B %Y %H:%M WIB')}")
    print(f"Total pasaran: {len(PASARAN)}")
    print(f"{'='*60}\n")

    try:
        with open('result.json', 'r', encoding='utf-8') as f:
            saved = json.load(f)
        print(f"Data lama: {len([k for k in saved if not k.startswith('_')])} pasaran\n")
    except Exception:
        saved = {}
        print("Tidak ada data lama.\n")

    result_data = dict(saved)

    for key, (path, name) in PASARAN.items():
        print(f"Fetching {key.upper()} <- {BASE+path}")
        entry = fetch_pasaran(key, path, name)
        if entry['result'] != '----':
            # Dapat result baru yang valid
            result_data[key] = entry
        elif key not in result_data:
            # Belum ada data lama sama sekali
            result_data[key] = entry
        else:
            old_result = result_data[key].get('result', '')
            if is_fake(old_result):
                # Data lama juga salah (tahun/fake) → buang, pakai ----
                print(f"  [{key.upper():6s}] Data lama '{old_result}' INVALID, reset ke ----")
                result_data[key] = entry
            else:
                print(f"  [{key.upper():6s}] Pakai data lama: {old_result}")

    result_data['_meta'] = {
        'updated': NOW.strftime('%Y-%m-%d %H:%M WIB'),
        'date':    TODAY,
        'total':   len(PASARAN),
    }

    with open('result.json', 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)

    ok = [k for k, v in result_data.items()
          if not k.startswith('_') and re.match(r'^\d{4}$', v.get('result', ''))]
    print(f"\n{'='*60}")
    print(f"result.json tersimpan | Valid: {len(ok)} | Belum: {len(PASARAN)-len(ok)}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
