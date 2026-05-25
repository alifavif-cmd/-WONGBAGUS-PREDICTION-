"""
backfill_history.py — Seed history 30 hari sekaligus ke result.json
Jalankan SEKALI saja, lalu fetch_all.py jalan normal tiap hari.

Usage:
    python backfill_history.py               # semua pasaran
    python backfill_history.py hk sgp sdy   # pasaran tertentu saja
"""

import requests
import json
import re
import time
import sys
import urllib3
urllib3.disable_warnings()

from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

# ===== CONFIG =====
HISTORY_MAX  = 30
RESULT_FILE  = 'result.json'
BASE         = 'https://angkanet18.com'
DIRECT_IP    = '159.65.133.131'
DELAY        = 1.0      # detik antar request (jangan terlalu cepat)

WIB  = timezone(timedelta(hours=7))
NOW  = datetime.now(WIB)

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8',
}

# Salin dari fetch_all.py
PASARAN = {
    'hk':   ('/data-pengeluaran-togel-hongkong-pools/',    'Hongkong Pools'),
    'hkl':  ('/data-pengeluaran-togel-hklotto/',           'Hongkong Lotto'),
    'sgp':  ('/data-pengeluaran-togel-singapore/',         'Singapore'),
    'sdy':  ('/data-pengeluaran-togel-sydney-pools/',      'Sydney Pools'),
    'sdl':  ('/data-pengeluaran-togel-sdlotto/',           'Sydney Lotto'),
    'kam':  ('/data-pengeluaran-togel-magnum-cambodia/',   'Kamboja'),
    'bull': ('/data-pengeluaran-togel-bullseye/',          'Bullseye NZ'),
    'chn':  ('/data-pengeluaran-togel-chinapools/',        'China Pools'),
    'jpn':  ('/data-pengeluaran-togel-japan/',             'Japan'),
    'twn':  ('/data-pengeluaran-togel-taiwan/',            'Taiwan'),
    'pcso': ('/data-pengeluaran-togel-pcso/',              'PCSO'),
    'mac1': ('/data-pengeluaran-togel-toto-macau-1/',      'Toto Macau 13'),
    'mac2': ('/data-pengeluaran-togel-toto-macau-2/',      'Toto Macau 16'),
    'mac3': ('/data-pengeluaran-togel-toto-macau-3/',      'Toto Macau 19'),
    'mac4': ('/data-pengeluaran-togel-toto-macau-4/',      'Toto Macau 22'),
    'mac5': ('/data-pengeluaran-togel-toto-macau-5/',      'Toto Macau 00'),
    'mac6': ('/data-pengeluaran-togel-toto-macau-6/',      'Toto Macau 23'),
    'mrq3':  ('/data-pengeluaran-togel-morocco-quatro-03-00-wib/', 'Morocco 03:00'),
    'mrq18': ('/data-pengeluaran-togel-morocco-quatro-18-00-wib/', 'Morocco 18:00'),
    'mrq21': ('/data-pengeluaran-togel-morocco-quatro-21-00-wib/', 'Morocco 21:00'),
    'mrq23': ('/data-pengeluaran-togel-morocco-quatro-23-59-wib/', 'Morocco 23:59'),
    'ger':  ('/data-pengeluaran-togel-germany-plus5/',     'Germany Plus5'),
    'or4':  ('/data-pengeluaran-togel-oregon-04-00-wib/',  'Oregon 04:00'),
    'or7':  ('/data-pengeluaran-togel-oregon-07-00-wib/',  'Oregon 07:00'),
    'or10': ('/data-pengeluaran-togel-oregon-10-00-wib/',  'Oregon 10:00'),
    'or13': ('/data-pengeluaran-togel-oregon-13-00-wib/',  'Oregon 13:00'),
    'ncd':  ('/data-pengeluaran-togel-north-carolina-day/',     'NC Day'),
    'nce':  ('/data-pengeluaran-togel-north-carolina-evening/', 'NC Evening'),
    'geom': ('/data-pengeluaran-togel-georgia-midday/',    'Georgia Midday'),
    'geoe': ('/data-pengeluaran-togel-georgia-evening/',   'Georgia Evening'),
    'geon': ('/data-pengeluaran-togel-georgia-night/',     'Georgia Night'),
    'txd':  ('/data-pengeluaran-togel-texas-day/',         'Texas Day'),
    'txmr': ('/data-pengeluaran-togel-texas-morning/',     'Texas Morning'),
    'txe':  ('/data-pengeluaran-togel-texas-evening/',     'Texas Evening'),
    'txn':  ('/data-pengeluaran-togel-texas-night/',       'Texas Night'),
    'nyd':  ('/data-pengeluaran-togel-new-york-midday/',   'New York Midday'),
    'nye':  ('/data-pengeluaran-togel-new-york-evening/',  'New York Evening'),
    'njm':  ('/data-pengeluaran-togel-new-jersey-midday/', 'NJ Midday'),
    'nje':  ('/data-pengeluaran-togel-new-jersey-evening/','NJ Evening'),
    'flm':  ('/data-pengeluaran-togel-florida-midday/',    'Florida Midday'),
    'fle':  ('/data-pengeluaran-togel-florida-evening/',   'Florida Evening'),
    'ilm':  ('/data-pengeluaran-togel-illinois-midday/',   'Illinois Midday'),
    'ile':  ('/data-pengeluaran-togel-illinois-evening/',  'Illinois Evening'),
    'indm': ('/data-pengeluaran-togel-indiana-midday/',    'Indiana Midday'),
    'inde': ('/data-pengeluaran-togel-indiana-evening/',   'Indiana Evening'),
    'kym':  ('/data-pengeluaran-togel-kentucky-midday/',   'Kentucky Midday'),
    'kye':  ('/data-pengeluaran-togel-kentucky-evening/',  'Kentucky Evening'),
    'mdm':  ('/data-pengeluaran-togel-maryland-midday/',   'Maryland Midday'),
    'mde':  ('/data-pengeluaran-togel-maryland-evening/',  'Maryland Evening'),
    'mim':  ('/data-pengeluaran-togel-michigan-midday/',   'Michigan Midday'),
    'mie':  ('/data-pengeluaran-togel-michigan-evening/',  'Michigan Evening'),
    'mom':  ('/data-pengeluaran-togel-missouri-midday/',   'Missouri Midday'),
    'moe':  ('/data-pengeluaran-togel-missouri-evening/',  'Missouri Evening'),
    'wdm':  ('/data-pengeluaran-togel-washington-dc-midday/',  'WDC Midday'),
    'wde':  ('/data-pengeluaran-togel-washington-dc-evening/', 'WDC Evening'),
    'ctd':  ('/data-pengeluaran-togel-connecticut-day/',   'Connecticut Day'),
    'ctn':  ('/data-pengeluaran-togel-connecticut-night/', 'Connecticut Night'),
    'vad':  ('/data-pengeluaran-togel-virginia-day/',      'Virginia Day'),
    'van':  ('/data-pengeluaran-togel-virginia-night/',    'Virginia Night'),
    'tnm':  ('/data-pengeluaran-togel-tennesse-midday/',   'Tennessee Midday'),
    'tne':  ('/data-pengeluaran-togel-tennesse-evening/',  'Tennessee Evening'),
    'tnmr': ('/data-pengeluaran-togel-tennesse-morning/',  'Tennessee Morning'),
    'cal':  ('/data-pengeluaran-togel-california/',        'California'),
    'wie':  ('/data-pengeluaran-togel-wisconsin-evening/', 'Wisconsin Evening'),
}

FAKE_PATTERNS = [
    r'^1234$', r'^2345$', r'^3456$', r'^4567$', r'^5678$',
    r'^6789$', r'^7890$', r'^8901$', r'^9012$', r'^0123$',
    r'^(\d)\1{3}$',
]

def is_fake(result):
    if not result or not re.match(r'^\d{4}$', result):
        return True
    try:
        n = int(result)
        if 1800 <= n <= 2099:
            return True
    except Exception:
        pass
    return any(re.match(p, result) for p in FAKE_PATTERNS)


# ===== EKSTRAK SEMUA BARIS HISTORIS =====
def extract_all_rows(html):
    """
    Berbeda dari fetch_all.py yang cuma ambil baris terbaru,
    fungsi ini mengembalikan SEMUA baris valid sebagai list:
    [{'date': 'YYYY-MM-DD', 'result': '1234'}, ...]
    Diurutkan descending (terbaru dulu).
    """
    if not html or len(html) < 200:
        return []

    soup = BeautifulSoup(html, 'html.parser')
    date_pat = re.compile(
        r'^(?:(\d{2})[/-](\d{2})[/-](\d{4})|(\d{4})[/-](\d{2})[/-](\d{2}))$'
    )

    # ── Strategy A: paito-row-item ──
    all_items = soup.find_all(class_='paito-row-item')
    row_map = {}
    for item in all_items:
        row_el = item.parent
        row_id = id(row_el)
        if row_id not in row_map:
            row_map[row_id] = {'date': None, 'result': None, 'order': len(row_map)}
        text = item.get_text(strip=True)

        if row_map[row_id]['date'] is None:
            m = date_pat.match(text)
            if m:
                if m.group(1):
                    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
                else:
                    y, mo, d = int(m.group(4)), int(m.group(5)), int(m.group(6))
                row_map[row_id]['date'] = (y, mo, d)

        if row_map[row_id]['result'] is None:
            if re.match(r'^\d{4}$', text) and not is_fake(text):
                row_map[row_id]['result'] = text

    valid_rows = [
        r for r in row_map.values()
        if r['date'] is not None and r['result'] is not None
    ]

    if valid_rows:
        valid_rows.sort(key=lambda x: x['date'], reverse=True)
        return [
            {
                'date':   f"{r['date'][0]:04d}-{r['date'][1]:02d}-{r['date'][2]:02d}",
                'result': r['result'],
            }
            for r in valid_rows[:HISTORY_MAX]
        ]

    # ── Strategy B: scan tabel/list biasa ──
    rows = []
    for tr in soup.find_all(['tr', 'li']):
        cells = tr.find_all(['td', 'span', 'div', 'p'])
        date_found = None
        result_found = None
        for c in cells:
            t = c.get_text(strip=True)
            if date_found is None:
                m = date_pat.match(t)
                if m:
                    if m.group(1):
                        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
                    else:
                        y, mo, d = int(m.group(4)), int(m.group(5)), int(m.group(6))
                    date_found = (y, mo, d)
            if result_found is None and re.match(r'^\d{4}$', t) and not is_fake(t):
                result_found = t
        if date_found and result_found:
            rows.append({
                'date':   f"{date_found[0]:04d}-{date_found[1]:02d}-{date_found[2]:02d}",
                'result': result_found,
            })

    # Deduplicate by date
    seen = set()
    deduped = []
    for r in rows:
        if r['date'] not in seen:
            seen.add(r['date'])
            deduped.append(r)

    deduped.sort(key=lambda x: x['date'], reverse=True)
    return deduped[:HISTORY_MAX]


# ===== FETCH HTML SATU PASARAN =====
def fetch_html(path):
    urls = [
        (BASE + path,                  dict(HEADERS)),
        (f'https://{DIRECT_IP}{path}', {**HEADERS, 'Host': 'angkanet18.com'}),
    ]
    for url, hdrs in urls:
        try:
            time.sleep(DELAY)
            r = requests.get(url, headers=hdrs, timeout=20, verify=False, allow_redirects=True)
            if r.status_code == 525:
                continue
            r.raise_for_status()
            if len(r.text) > 500:
                return r.text
        except Exception as e:
            print(f"    WARN {url}: {e}")
    return None


# ===== MERGE HISTORY =====
def merge_history(existing: list, new_rows: list) -> list:
    """
    Gabungkan history lama + baris baru, deduplicate by date,
    sort descending, potong HISTORY_MAX.
    """
    combined = {h['date']: h['result'] for h in existing}
    for r in new_rows:
        if r['date'] not in combined:
            combined[r['date']] = r['result']
        # Kalau tanggal sudah ada, pakai yang sudah ada (jangan overwrite)

    merged = [
        {'date': d, 'result': res}
        for d, res in combined.items()
    ]
    merged.sort(key=lambda x: x['date'], reverse=True)
    return merged[:HISTORY_MAX]


# ===== MAIN =====
def main():
    # Filter pasaran dari argumen CLI (opsional)
    filter_keys = [k.lower() for k in sys.argv[1:]] if len(sys.argv) > 1 else None
    targets = {
        k: v for k, v in PASARAN.items()
        if filter_keys is None or k in filter_keys
    }

    print(f"\n{'='*60}")
    print(f"backfill_history.py — {NOW.strftime('%A, %d %B %Y %H:%M WIB')}")
    print(f"Target: {len(targets)} pasaran  |  History max: {HISTORY_MAX}")
    print(f"{'='*60}\n")

    # Load result.json yang ada
    try:
        with open(RESULT_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"Loaded {RESULT_FILE}: {len([k for k in data if not k.startswith('_')])} pasaran\n")
    except FileNotFoundError:
        data = {}
        print(f"WARN: {RESULT_FILE} tidak ditemukan, akan dibuat baru.\n")
    except Exception as e:
        print(f"ERROR load {RESULT_FILE}: {e}")
        return

    stats = {'ok': 0, 'partial': 0, 'skip': 0, 'fail': 0}

    for key, (path, name) in targets.items():
        existing_entry = data.get(key, {})
        existing_hist  = existing_entry.get('history', [])
        old_len = len(existing_hist)

        # Kalau sudah penuh, skip
        if old_len >= HISTORY_MAX:
            print(f"  [{key.upper():6s}] SKIP — history sudah {old_len} entry")
            stats['skip'] += 1
            continue

        print(f"  [{key.upper():6s}] Fetching {BASE+path}  (history lama: {old_len})")

        html = fetch_html(path)
        if not html:
            print(f"  [{key.upper():6s}] FAIL — tidak bisa fetch HTML")
            stats['fail'] += 1
            continue

        rows = extract_all_rows(html)
        if not rows:
            print(f"  [{key.upper():6s}] FAIL — tidak ada baris ditemukan")
            stats['fail'] += 1
            continue

        new_hist = merge_history(existing_hist, rows)
        new_len  = len(new_hist)

        if key not in data:
            # Pasaran belum ada di result.json sama sekali
            data[key] = {
                'result':  rows[0]['result'],
                'tgl':     rows[0]['date'][8:] + '/' + rows[0]['date'][5:7],  # dd/mm
                'status':  'sudah',
                'name':    name,
                'updated': NOW.strftime('%H:%M WIB') + ' [backfill]',
                'history': new_hist,
            }
        else:
            data[key]['history'] = new_hist

        added = new_len - old_len
        print(f"  [{key.upper():6s}] OK — {new_len} entry (+{added} baru)  "
              f"[{rows[0]['date']} → {rows[-1]['date']}]")

        if new_len >= HISTORY_MAX:
            stats['ok'] += 1
        else:
            stats['partial'] += 1

    # Update _meta
    data['_meta'] = data.get('_meta', {})
    data['_meta']['backfill_run'] = NOW.strftime('%Y-%m-%d %H:%M WIB')
    data['_meta']['history_max']  = HISTORY_MAX

    with open(RESULT_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"Selesai. {RESULT_FILE} tersimpan.")
    print(f"  Penuh (={HISTORY_MAX}): {stats['ok']}")
    print(f"  Partial (<{HISTORY_MAX}): {stats['partial']}")
    print(f"  Skip (sudah penuh): {stats['skip']}")
    print(f"  Gagal: {stats['fail']}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
