#!/usr/bin/env python3
"""
Auto-fetch HK Pools result dan update hk.json
WONGBAGUS PREDICTION - Auto Update System
"""

import json
import os
import re
import sys
from datetime import datetime, timezone, timedelta
import urllib.request
import urllib.error

# Timezone WIB (UTC+7)
WIB = timezone(timedelta(hours=7))

DAYS_ID = {
    0: 'SEN', 1: 'SEL', 2: 'RAB', 3: 'KAM',
    4: 'JUM', 5: 'SAB', 6: 'MIN'
}

DATA_FILE = os.path.join(os.path.dirname(__file__), '..', 'data', 'hk.json')


def fetch_url(url, timeout=10):
    try:
        req = urllib.request.Request(url, headers={
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'application/json, text/html, */*',
        })
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"  [FAIL] {url}: {e}")
        return None


def parse_4d(text):
    """Cari pola 4 digit berurutan dari text"""
    if not text:
        return None
    # Cari 4 digit berurutan
    matches = re.findall(r'\b(\d{4})\b', text)
    if matches:
        return matches[0]
    return None


def fetch_hk_result():
    """
    Coba ambil result HK dari beberapa sumber.
    Kembalikan string 4D atau None.
    """
    today = datetime.now(WIB)
    date_str = today.strftime('%Y-%m-%d')
    print(f"Fetching HK result for {date_str}...")

    # ---- SUMBER 1: JSON API publik ----
    sources_api = [
        "https://hk4d.net/api/result/today",
        "https://api.hktoto.net/latest",
        "https://togelsydney.com/api/hk/latest.json",
    ]
    for url in sources_api:
        print(f"  Trying API: {url}")
        raw = fetch_url(url)
        if raw:
            try:
                data = json.loads(raw)
                # Coba berbagai key yang mungkin
                for key in ['result', 'output', 'number', 'prize', '4d', 'keluaran']:
                    if key in data:
                        val = str(data[key]).strip()
                        if re.match(r'^\d{4}$', val):
                            print(f"  [OK] Found via API key '{key}': {val}")
                            return val
            except Exception:
                result = parse_4d(raw)
                if result:
                    print(f"  [OK] Found in raw: {result}")
                    return result

    # ---- SUMBER 2: HTML scraping ----
    sources_html = [
        ("https://hkresult.net/", r'result["\s:>]+(\d{4})'),
        ("https://live.hkpool.net/", r'(\d{4})'),
        ("https://totobet.asia/hk/", r'(\d{4})'),
    ]
    for url, pattern in sources_html:
        print(f"  Trying HTML: {url}")
        raw = fetch_url(url)
        if raw:
            match = re.search(pattern, raw, re.IGNORECASE)
            if match:
                val = match.group(1)
                print(f"  [OK] Found via scrape: {val}")
                return val

    print("  [WARN] Semua sumber gagal, result tidak ditemukan.")
    return None


def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return {"market": "Hongkong Pools", "lastUpdate": "", "results": []}


def save_data(data):
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
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
        # Tetap update lastUpdate
        data['lastUpdate'] = now.strftime('%Y-%m-%d %H:%M WIB')
        save_data(data)
        return

    result_4d = fetch_hk_result()

    if not result_4d:
        print("Tidak ada result baru, tidak update.")
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
    results.insert(0, new_entry)  # terbaru di atas
    # Simpan max 365 data
    results = results[:365]

    data['results'] = results
    data['lastUpdate'] = now.strftime('%Y-%m-%d %H:%M WIB')
    data['market'] = 'Hongkong Pools'

    save_data(data)
    print(f"[SUCCESS] Result HK {date_str}: {result_4d}")


if __name__ == '__main__':
    main()
