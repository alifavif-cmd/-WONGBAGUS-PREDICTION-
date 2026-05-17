#!/usr/bin/env python3
"""
Auto-fetch HK Pools result
WONGBAGUS PREDICTION
"""

import json, os, re, sys, ssl
from datetime import datetime, timezone, timedelta
import urllib.request

WIB = timezone(timedelta(hours=7))
DAYS_ID = {0:'SEN',1:'SEL',2:'RAB',3:'KAM',4:'JUM',5:'SAB',6:'MIN'}
DATA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'hk.json')

CTX = ssl.create_default_context()
CTX.check_hostname = False
CTX.verify_mode = ssl.CERT_NONE

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9',
}

def fetch_url(url, timeout=20):
    try:
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=timeout, context=CTX) as r:
            raw = r.read().decode('utf-8', errors='ignore')
            print(f"  [OK] {url} ({len(raw)} chars)")
            return raw
    except Exception as e:
        print(f"  [FAIL] {url}: {e}")
        return None

def find_4d_near_date(raw, date_str):
    d,m,y = date_str.split('-')
    pats = [
        date_str + r'[^\d]{0,30}?(\d{4})',
        d+r'[-/]'+m+r'[-/]'+y+r'[^\d]{0,30}?(\d{4})',
        y+r'[-/]'+m+r'[-/]'+d+r'[^\d]{0,30}?(\d{4})',
    ]
    for pat in pats:
        m2 = re.search(pat, raw)
        if m2:
            val = m2.group(1)
            if not re.match(r'^(202|201|200|199)', val):
                return val
    return None

def fetch_hk_result(date_str):
    sources = [
        'http://159.65.133.131/paito-warna-hongkong-pools/',
        'http://159.65.133.131/',
        'https://159.65.133.131/paito-warna-hongkong-pools/',
        'https://totobet.net/hongkong/',
        'https://togelbagus.com/hk/',
        'https://www.lotterypost.com/results/hk',
    ]
    for url in sources:
        print(f"  Trying: {url}")
        raw = fetch_url(url)
        if not raw:
            continue
        val = find_4d_near_date(raw, date_str)
        if val:
            print(f"  [FOUND] {date_str} = {val}")
            return val
    return None

def load_data():
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {"market":"Hongkong Pools","lastUpdate":"","results":[]}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  [SAVED] hk.json")

def main():
    now = datetime.now(WIB)
    if now.hour < 23:
        print(f"Jam {now.hour}:{now.minute:02d} WIB - Skip, belum 23:00.")
        sys.exit(0)

    date_str = now.strftime('%Y-%m-%d')
    day_str = DAYS_ID[now.weekday()]
    data = load_data()
    existing = {r['date'] for r in data.get('results',[])}

    if date_str in existing:
        print(f"Result {date_str} sudah ada.")
        sys.exit(0)

    print(f"Fetching HK {date_str}...")
    result_4d = fetch_hk_result(date_str)

    if not result_4d:
        print("Gagal fetch result.")
        sys.exit(1)

    entry = {
        "date": date_str, "day": day_str,
        "result": result_4d,
        "as": result_4d[0], "kop": result_4d[1],
        "kepala": result_4d[2], "ekor": result_4d[3]
    }
    results = data.get('results', [])
    results.insert(0, entry)
    data['results'] = results[:365]
    data['lastUpdate'] = now.strftime('%Y-%m-%d %H:%M WIB')
    data['market'] = 'Hongkong Pools'
    save_data(data)
    print(f"[SUCCESS] {date_str}: {result_4d}")

if __name__ == '__main__':
    main()
