#!/usr/bin/env python3
"""
Auto-fetch HK Pools dari angkanet paito harian
WONGBAGUS PREDICTION
"""

import json, os, re, sys
from datetime import datetime, timezone, timedelta
import urllib.request

WIB = timezone(timedelta(hours=7))
DAYS_ID = {0:'SEN',1:'SEL',2:'RAB',3:'KAM',4:'JUM',5:'SAB',6:'MIN'}
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hk.json')
BASE = 'https://159.65.133.131'

def fetch_url(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Accept': 'text/html,*/*',
            'Referer': BASE,
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  [FAIL] {url}: {e}")
        return None

def fetch_all_hk():
    """Ambil semua data HK dari paito harian angkanet"""
    urls = [
        f"{BASE}/paito-warna-hongkong-pools/",
        f"{BASE}/paito-harian/?pasaran=hongkong",
        f"{BASE}/data-pengeluaran-togel/hongkong/",
    ]
    for url in urls:
        print(f"  Trying: {url}")
        raw = fetch_url(url)
        if not raw:
            continue
        # Cari semua pasangan tanggal + 4 digit
        pattern = r'(\d{2}-\d{2}-\d{4})\D{0,20}?(\d{4})'
        matches = re.findall(pattern, raw)
        if matches:
            print(f"  [OK] Found {len(matches)} entries from {url}")
            return matches
        # Format tanggal yyyy-mm-dd
        pattern2 = r'(\d{4}-\d{2}-\d{2})\D{0,20}?(\d{4})'
        matches2 = re.findall(pattern2, raw)
        if matches2:
            print(f"  [OK] Found {len(matches2)} entries from {url}")
            return [(f"{d[8:10]}-{d[5:7]}-{d[0:4]}", r) for d, r in matches2]
    return []

def parse_date(date_str):
    """Parse dd-mm-yyyy ke yyyy-mm-dd"""
    try:
        if '-' in date_str and len(date_str) == 10:
            parts = date_str.split('-')
            if len(parts[2]) == 4:  # dd-mm-yyyy
                return f"{parts[2]}-{parts[1]}-{parts[0]}"
            else:  # yyyy-mm-dd
                return date_str
    except:
        pass
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

    if now.hour < 23:
        print(f"Jam {now.hour}:{now.minute:02d} WIB - Belum jam 23:00, skip.")
        sys.exit(0)

    data = load_data()
    existing_dates = {r['date'] for r in data.get('results', [])}

    print("Fetching HK data dari angkanet...")
    raw_entries = fetch_all_hk()

    if not raw_entries:
        print("Gagal ambil data dari angkanet.")
        sys.exit(1)

    new_count = 0
    results = data.get('results', [])

    for raw_date, result_4d in raw_entries:
        date_str = parse_date(raw_date)
        if not date_str:
            continue
        if date_str in existing_dates:
            continue
        if not re.match(r'^\d{4}$', result_4d):
            continue

        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
        except:
            continue

        day_str = DAYS_ID[dt.weekday()]
        new_entry = {
            "date": date_str,
            "day": day_str,
            "result": result_4d,
            "as": result_4d[0],
            "kop": result_4d[1],
            "kepala": result_4d[2],
            "ekor": result_4d[3]
        }
        results.append(new_entry)
        existing_dates.add(date_str)
        new_count += 1
        print(f"  + {date_str}: {result_4d}")

    if new_count == 0:
        print("Tidak ada data baru.")
        sys.exit(0)

    # Sort terbaru di atas
    results.sort(key=lambda x: x['date'], reverse=True)
    data['results'] = results[:365]
    data['lastUpdate'] = now.strftime('%Y-%m-%d %H:%M WIB')
    data['market'] = 'Hongkong Pools'

    save_data(data)
    print(f"[SUCCESS] +{new_count} entries baru dari angkanet")

if __name__ == '__main__':
    main()
