#!/usr/bin/env python3
"""
Auto-fetch HK Pools result dari angkanet
WONGBAGUS PREDICTION
"""

import json, os, re, sys
from datetime import datetime, timezone, timedelta
import urllib.request

WIB = timezone(timedelta(hours=7))
DAYS_ID = {0:'SEN',1:'SEL',2:'RAB',3:'KAM',4:'JUM',5:'SAB',6:'MIN'}
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hk.json')

ANGKANET = 'https://159.65.133.131'

def fetch_url(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/json,*/*',
            'Referer': ANGKANET,
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  [FAIL] {url}: {e}")
        return None

def fetch_hk_result(date_str):
    # Coba ambil dari paito harian HK angkanet
    urls = [
        f"{ANGKANET}/paito-warna-hongkong-pools/",
        f"{ANGKANET}/data-pengeluaran-togel/hongkong/",
        f"{ANGKANET}/paito-harian/",
    ]
    for url in urls:
        print(f"  Trying: {url}")
        raw = fetch_url(url)
        if not raw:
            continue
        # Cari tanggal hari ini dan ambil angka setelahnya
        pattern = date_str + r'[^\d]*(\d{4})'
        match = re.search(pattern, raw)
        if match:
            val = match.group(1)
            print(f"  [OK] Angkanet {url}: {val}")
            return val
        # Coba pattern tanggal format lain (dd-mm-yyyy)
        d, m, y = date_str.split('-')
        alt_date = f"{d}-{m}-{y}"
        pattern2 = alt_date + r'[^\d]*(\d{4})'
        match2 = re.search(pattern2, raw)
        if match2:
            val = match2.group(1)
            print(f"  [OK] Angkanet alt: {val}")
            return val

    print("  [WARN] Tidak ketemu di angkanet.")
    return None

def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"market": "Hongkong Pools", "lastUpdate": "", "results": []}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [SAVED] {DATA_FILE}")

def main():
    now = datetime.now(WIB)

    # Jangan fetch sebelum jam 23:00 WIB
    if now.hour < 23:
        print(f"Jam {now.hour}:{now.minute:02d} WIB - Belum jam 23:00, skip.")
        sys.exit(0)

    date_str = now.strftime('%Y-%m-%d')
    day_str = DAYS_ID[now.weekday()]

    data = load_data()
    existing_dates = {r['date'] for r in data.get('results', [])}

    if date_str in existing_dates:
        print(f"Result {date_str} sudah ada.")
        sys.exit(0)

    print(f"Fetching HK result {date_str} dari angkanet...")
    result_4d = fetch_hk_result(date_str)

    if not result_4d:
        print("Result tidak ditemukan.")
        sys.exit(1)

    new_entry = {
        "date": date_str,
        "day": day_str,
        "result": result_4d,
        "as": result_4d[0],
        "kop": result_4d[1],
        "kepala": result_4d[2],
        "ekor": result_4d[3]
    }

    results = data.get('results', [])
    results.insert(0, new_entry)
    data['results'] = results[:365]
    data['lastUpdate'] = now.strftime('%Y-%m-%d %H:%M WIB')
    data['market'] = 'Hongkong Pools'

    save_data(data)
    print(f"[SUCCESS] {date_str}: {result_4d}")

if __name__ == '__main__':
    main()
