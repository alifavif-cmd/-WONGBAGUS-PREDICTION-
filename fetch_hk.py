#!/usr/bin/env python3
"""
Auto-fetch HK Pools result dan update hk.json
WONGBAGUS PREDICTION - Auto Update System
Sumber: hongkongpools.com + backup sources
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
import urllib.request

WIB = timezone(timedelta(hours=7))

DAYS_ID = {
    0: 'SEN', 1: 'SEL', 2: 'RAB', 3: 'KAM',
    4: 'JUM', 5: 'SAB', 6: 'MIN'
}

DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hk.json')


def fetch_url(url, timeout=15):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/json,*/*',
            'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8',
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  [FAIL] {url}: {e}")
        return None


def fetch_hk_result():
    today = datetime.now(WIB)
    date_str = today.strftime('%Y-%m-%d')
    print(f"Fetching HK result for {date_str}...")

    # SUMBER 1: totobet.net - reliable scraping source
    print("  Trying totobet.net...")
    raw = fetch_url("https://totobet.net/hongkong/")
    if raw:
        # Cari result 4D pattern
        match = re.search(r'result[^\d]*(\d{4})', raw, re.IGNORECASE)
        if match:
            val = match.group(1)
            print(f"  [OK] totobet.net: {val}")
            return val
        # Pattern lain
        matches = re.findall(r'\b(\d{4})\b', raw)
        if matches:
            # Filter angka yang masuk akal (bukan tahun dll)
            for m in matches[:10]:
                if not m.startswith('202') and not m.startswith('201'):
                    print(f"  [OK] totobet.net raw: {m}")
                    return m

    # SUMBER 2: arenaskor.com
    print("  Trying arenaskor.com...")
    raw = fetch_url("https://hk.arenaskor.com/")
    if raw:
        match = re.search(r'(\d{4})', raw)
        if match:
            val = match.group(1)
            if not val.startswith('202'):
                print(f"  [OK] arenaskor: {val}")
                return val

    # SUMBER 3: live.hongkongpools.com
    print("  Trying hongkongpools...")
    raw = fetch_url("https://www.hongkongpools.com/")
    if raw:
        # Cari pola angka 4D
        match = re.search(r'(\d{4})', raw)
        if match:
            val = match.group(1)
            if not val.startswith('202'):
                print(f"  [OK] hongkongpools: {val}")
                return val

    print("  [WARN] Semua sumber gagal.")
    return None


def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {"market": "Hongkong Pools", "lastUpdate": "", "results": []}


def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [SAVED] {DATA_FILE}")


def main():
    now = datetime.now(WIB)
    date_str = now.strftime('%Y-%m-%d')
    day_str = DAYS_ID[now.weekday()]

    data = load_data()
    existing_dates = {r['date'] for r in data.get('results', [])}

    if date_str in existing_dates:
        print(f"Result {date_str} sudah ada, skip.")
        data['lastUpdate'] = now.strftime('%Y-%m-%d %H:%M WIB')
        save_data(data)
        return

    result_4d = fetch_hk_result()

    if not result_4d:
        print("Tidak ada result baru.")
        sys.exit(0)

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
    results = results[:365]

    data['results'] = results
    data['lastUpdate'] = now.strftime('%Y-%m-%d %H:%M WIB')
    data['market'] = 'Hongkong Pools'

    save_data(data)
    print(f"[SUCCESS] Result HK {date_str}: {result_4d}")


if __name__ == '__main__':
    main()
