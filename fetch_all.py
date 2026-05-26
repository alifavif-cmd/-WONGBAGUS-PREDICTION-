"""
fetch_all.py — Fetch 65 pasaran togel dari angkanet.com
Simpan ke result.json, dibaca langsung oleh index.html
v5.0: SINGLE BeautifulSoup parse per halaman (2x lebih cepat dari v4)
      - extract_result_and_rows() gabung result+history dalam 1 parse
      - save result.json SEBELUM backfill (data aman meski timeout)
      - time budget: skip backfill jika < 90s tersisa
      - timeout request: 4s (dari 8s)
      - sys.stdout line_buffering untuk log real-time di Actions
"""

import sys
import requests
import json
import re
import time
import urllib3
urllib3.disable_warnings()
sys.stdout.reconfigure(line_buffering=True)

from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

# Timer global
_SCRIPT_START = time.monotonic()
def _elapsed():
    return time.monotonic() - _SCRIPT_START
def _time_left(budget=270):
    return budget - _elapsed()

# ===== TIMEZONE =====
WIB = timezone(timedelta(hours=7))
NOW = datetime.now(WIB)
TODAY = NOW.strftime('%d/%m')

BASE      = 'https://angkanet18.com'
DIRECT_IP = '159.65.133.131'

HISTORY_MAX = 30

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

PASARAN_MALAM = {'mrq23', 'mac6', 'txn', 'geon', 'ctn', 'van', 'tne'}

# Pasaran yang WAJIB fetch individual (skip paito-harian — sering salah parsing)
SKIP_PAITO_HARIAN = {'hk', 'sgp', 'sdy', 'sdl', 'hkl', 'kam', 'bull', 'chn', 'jpn', 'twn', 'pcso'}

TODAY_TUPLE = (NOW.year, NOW.month, NOW.day)
TODAY_STR   = f"{TODAY_TUPLE[0]:04d}-{TODAY_TUPLE[1]:02d}-{TODAY_TUPLE[2]:02d}"

MANUAL_OVERRIDE = {}

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8',
}

FAKE_PATTERNS = [
    r'^1234$', r'^2345$', r'^3456$', r'^4567$', r'^5678$',
    r'^6789$', r'^7890$', r'^8901$', r'^9012$', r'^0123$',
    r'^(\d)\1{3}$',
]

def is_year(result):
    try:
        n = int(result)
        return 1800 <= n <= 2099
    except Exception:
        return False

from datetime import date as _date_cls

def _is_plausible_date(d_tuple, max_past_days=400):
    """True jika tanggal masuk akal: tidak lebih dari max_past_days hari lalu, tidak di masa depan."""
    try:
        dt   = _date_cls(*d_tuple)
        today = _date_cls(*TODAY_TUPLE)
        diff  = (today - dt).days
        return 0 <= diff <= max_past_days
    except Exception:
        return False

def is_fake(result):
    if not result or not re.match(r'^\d{4}$', result):
        return True
    if is_year(result):
        return True
    return any(re.match(p, result) for p in FAKE_PATTERNS)


# ===== HISTORY HELPER =====
def update_history(old_data: dict, new_result: str, date_str: str) -> list:
    history = old_data.get('history', [])
    existing_idx = next(
        (i for i, h in enumerate(history) if h.get('date') == date_str), None)
    if existing_idx is not None:
        history[existing_idx] = {'date': date_str, 'result': new_result}
    else:
        history = [{'date': date_str, 'result': new_result}] + history
    history.sort(key=lambda h: h.get('date', ''), reverse=True)
    return history[:HISTORY_MAX]


def merge_rows_into_history(existing_history: list, new_rows: list) -> list:
    combined = {h['date']: h['result'] for h in existing_history}
    for r in new_rows:
        if r['date'] not in combined:
            combined[r['date']] = r['result']
    merged = [{'date': d, 'result': res} for d, res in combined.items()]
    merged.sort(key=lambda x: x['date'], reverse=True)
    return merged[:HISTORY_MAX]


# ===== CORE: SINGLE-PARSE → RESULT + ALL ROWS =====
_DATE_PAT = re.compile(
    r'^(?:(\d{2})[/-](\d{2})[/-](\d{4})|(\d{4})[/-](\d{2})[/-](\d{2}))$'
)

def _parse_date(text):
    m = _DATE_PAT.match(text.strip())
    if not m:
        return None
    if m.group(1):
        return (int(m.group(3)), int(m.group(2)), int(m.group(1)))
    return (int(m.group(4)), int(m.group(5)), int(m.group(6)))

def _extract_4digit_from_paito_line(line_el):
    """Ambil angka 4-digit pertama yang valid dari .paito-line."""
    for ri in line_el.find_all(class_='paito-row-item'):
        t = ri.get_text(strip=True)
        if re.match(r'^\d{4}$', t) and not is_fake(t):
            return t
        digs = ri.find_all(class_='paito-digit')
        if len(digs) >= 4:
            candidate = ''.join(d.get_text(strip=True) for d in digs[:4])
            if re.match(r'^\d{4}$', candidate) and not is_fake(candidate):
                return candidate
    for el in line_el.find_all(True):
        t = el.get_text(strip=True)
        if re.match(r'^\d{4}$', t) and not is_fake(t):
            return t
    return None


def extract_result_and_rows(html):
    """
    Parse HTML SEKALI → return (fetch_date, result, all_rows).
    fetch_date: list [y,m,d] atau None
    result: string 4-digit atau None
    all_rows: [{'date': 'YYYY-MM-DD', 'result': '1234'}, ...]
    """
    if not html or len(html) < 200:
        return None, None, []

    soup = BeautifulSoup(html, 'html.parser')
    seen_dates = set()
    rows_out = []
    best_date = None
    best_result = None

    # ── Strategy A: .paito-line sebagai row container ──
    all_lines = soup.find_all(class_='paito-line')
    # Helper: cari tanggal di sibling elements saja (bukan seluruh find_all)
    def _find_date_near_line(line_el):
        """Cari tanggal di sibling atau parent langsung — TIDAK rekursif ke seluruh halaman."""
        parent = line_el.parent
        if parent is None:
            return None
        # Cek semua sibling langsung dari parent
        for sib in parent.children:
            if sib is line_el:
                continue
            t = sib.get_text(strip=True) if hasattr(sib, 'get_text') else str(sib).strip()
            d = _parse_date(t)
            if d and _is_plausible_date(d):   # filter: tanggal harus masuk akal
                return d
        # Naik 1 level: cek sibling dari parent
        grandparent = parent.parent
        if grandparent is None:
            return None
        for sib in grandparent.children:
            if sib is parent:
                continue
            t = sib.get_text(strip=True) if hasattr(sib, 'get_text') else str(sib).strip()
            d = _parse_date(t)
            if d and _is_plausible_date(d):
                return d
            # Cek children langsung dari sib (1 level dalam)
            if hasattr(sib, 'children'):
                for child in sib.children:
                    t2 = child.get_text(strip=True) if hasattr(child, 'get_text') else str(child).strip()
                    d2 = _parse_date(t2)
                    if d2 and _is_plausible_date(d2):
                        return d2
        return None

    if all_lines:
        for line in all_lines:
            result = _extract_4digit_from_paito_line(line)
            if not result:
                continue
            date_found = _find_date_near_line(line)

            if date_found and result:
                ds = f"{date_found[0]:04d}-{date_found[1]:02d}-{date_found[2]:02d}"
                if ds not in seen_dates:
                    seen_dates.add(ds)
                    rows_out.append({'date': ds, 'result': result})
                    if best_date is None or date_found > tuple(best_date) if best_date else True:
                        best_date = list(date_found)
                        best_result = result
            elif result and best_result is None:
                best_result = result

        if rows_out:
            rows_out.sort(key=lambda x: x['date'], reverse=True)
            # Filter ulang: pastikan tidak ada tanggal corrupt di rows
            rows_out = [r for r in rows_out
                        if _is_plausible_date(tuple(int(x) for x in r['date'].split('-')))]
            if rows_out:
                best_row = rows_out[0]
                bd = tuple(int(x) for x in best_row['date'].split('-'))
                return list(bd), best_row['result'], rows_out[:HISTORY_MAX]

        # Strategy A found result tapi tanpa tanggal valid → return dengan tanggal hari ini
        if best_result:
            return list(TODAY_TUPLE), best_result, []

    # ── Strategy B: paito-row-item grouping ──
    all_items = soup.find_all(class_='paito-row-item')
    if all_items:
        row_map = {}
        for item in all_items:
            row_el = item.parent
            rid = id(row_el)
            if rid not in row_map:
                row_map[rid] = {'date': None, 'result': None}
            digs = item.find_all(class_='paito-digit')
            text = item.get_text(strip=True)
            if len(digs) >= 4:
                candidate = ''.join(d.get_text(strip=True) for d in digs[:4])
                if re.match(r'^\d{4}$', candidate) and not is_fake(candidate):
                    if row_map[rid]['result'] is None:
                        row_map[rid]['result'] = candidate
            if row_map[rid]['date'] is None:
                d = _parse_date(text)
                if d and _is_plausible_date(d):   # filter: tanggal harus masuk akal
                    row_map[rid]['date'] = d
            if row_map[rid]['result'] is None and re.match(r'^\d{4}$', text) and not is_fake(text):
                row_map[rid]['result'] = text

        rows_B = [r for r in row_map.values() if r['date'] and r['result']]
        if rows_B:
            rows_B.sort(key=lambda x: x['date'], reverse=True)
            rows_out = [
                {'date': f"{r['date'][0]:04d}-{r['date'][1]:02d}-{r['date'][2]:02d}",
                 'result': r['result']}
                for r in rows_B[:HISTORY_MAX]
            ]
            bd = rows_B[0]['date']
            return list(bd), rows_B[0]['result'], rows_out

    # ── Strategy C: scan tabel/list ──
    rows_C = []
    seen_C = set()
    for tr in soup.find_all(['tr', 'li']):
        cells = tr.find_all(['td', 'span', 'div', 'b'])
        date_found = result_found = None
        for c in cells:
            t = c.get_text(strip=True)
            if date_found is None:
                d = _parse_date(t)
                if d and _is_plausible_date(d):
                    date_found = d
            if result_found is None and re.match(r'^\d{4}$', t) and not is_fake(t):
                result_found = t
        if date_found and result_found:
            ds = f"{date_found[0]:04d}-{date_found[1]:02d}-{date_found[2]:02d}"
            if ds not in seen_C:
                seen_C.add(ds)
                rows_C.append({'date': ds, 'result': result_found, '_d': date_found})

    if rows_C:
        rows_C.sort(key=lambda x: x['_d'], reverse=True)
        best = rows_C[0]
        all_rows = [{'date': r['date'], 'result': r['result']} for r in rows_C[:HISTORY_MAX]]
        return list(best['_d']), best['result'], all_rows

    # ── Fallback: angka 4 digit pertama ──
    for tag in soup.find_all(['span', 'td', 'div']):
        t = tag.get_text(strip=True)
        if re.match(r'^\d{4}$', t) and not is_fake(t):
            return None, t, []

    return None, None, []


# ===== PAITO HARIAN KEYWORD MAP =====
KEYWORD_MAP = [
    ('hongkong pool', 'hk'), ('hk pools', 'hk'), ('hk lotto', 'hkl'), ('hklotto', 'hkl'),
    ('singapore', 'sgp'), ('sydney pools', 'sdy'), ('sydney pool', 'sdy'),
    ('sydney lotto', 'sdl'), ('sdlotto', 'sdl'), ('magnum cambodia', 'kam'),
    ('kamboja', 'kam'), ('cambodia', 'kam'), ('bullseye', 'bull'),
    ('china pool', 'chn'), ('chinapool', 'chn'), ('japan', 'jpn'), ('taiwan', 'twn'),
    ('pcso', 'pcso'), ('toto macau 1', 'mac1'), ('macau 13', 'mac1'),
    ('toto macau 2', 'mac2'), ('macau 16', 'mac2'), ('toto macau 3', 'mac3'),
    ('macau 19', 'mac3'), ('toto macau 4', 'mac4'), ('macau 22', 'mac4'),
    ('toto macau 5', 'mac5'), ('macau 00', 'mac5'), ('toto macau 6', 'mac6'),
    ('macau 23', 'mac6'), ('morocco quatro 03', 'mrq3'), ('morocco 03', 'mrq3'),
    ('morocco quatro 18', 'mrq18'), ('morocco 18', 'mrq18'),
    ('morocco quatro 21', 'mrq21'), ('morocco 21', 'mrq21'),
    ('morocco quatro 23', 'mrq23'), ('morocco 23', 'mrq23'),
    ('germany', 'ger'), ('oregon 04', 'or4'), ('oregon 07', 'or7'),
    ('oregon 10', 'or10'), ('oregon 13', 'or13'),
    ('north carolina day', 'ncd'), ('nc day', 'ncd'),
    ('north carolina evening', 'nce'), ('nc evening', 'nce'),
    ('georgia midday', 'geom'), ('georgia mid', 'geom'),
    ('georgia evening', 'geoe'), ('georgia eve', 'geoe'),
    ('georgia night', 'geon'), ('texas morning', 'txmr'), ('texas day', 'txd'),
    ('texas evening', 'txe'), ('texas night', 'txn'),
    ('new york midday', 'nyd'), ('new york evening', 'nye'),
    ('new jersey midday', 'njm'), ('nj midday', 'njm'),
    ('new jersey evening', 'nje'), ('nj evening', 'nje'),
    ('florida midday', 'flm'), ('florida evening', 'fle'),
    ('illinois midday', 'ilm'), ('illinois evening', 'ile'),
    ('indiana midday', 'indm'), ('indiana evening', 'inde'),
    ('kentucky midday', 'kym'), ('kentucky evening', 'kye'),
    ('maryland midday', 'mdm'), ('maryland evening', 'mde'),
    ('michigan midday', 'mim'), ('michigan evening', 'mie'),
    ('missouri midday', 'mom'), ('missouri evening', 'moe'),
    ('washington dc midday', 'wdm'), ('wdc midday', 'wdm'),
    ('washington dc evening', 'wde'), ('wdc evening', 'wde'),
    ('connecticut day', 'ctd'), ('connecticut night', 'ctn'),
    ('virginia day', 'vad'), ('virginia night', 'van'),
    ('tennesse midday', 'tnm'), ('tennessee midday', 'tnm'),
    ('tennesse evening', 'tne'), ('tennessee evening', 'tne'),
    ('tennesse morning', 'tnmr'), ('tennessee morning', 'tnmr'),
    ('california', 'cal'), ('wisconsin evening', 'wie'),
]

def match_market(text):
    tl = text.lower()
    for kw, key in KEYWORD_MAP:
        if kw in tl:
            return key
    return None


# ===== PAITO HARIAN =====
PAITO_HARIAN_URL = f'{BASE}/paito-harian/'

def fetch_paito_harian():
    print(f"\n{'='*60}", flush=True)
    print(f"[PAITO-HARIAN] {PAITO_HARIAN_URL}", flush=True)
    print(f"{'='*60}", flush=True)

    html = None
    for url, hdrs in [
        (PAITO_HARIAN_URL, dict(HEADERS)),
        (f'https://{DIRECT_IP}/paito-harian/', {**HEADERS, 'Host': 'angkanet18.com'}),
    ]:
        try:
            time.sleep(0.1)
            r = requests.get(url, headers=hdrs, timeout=10, verify=False, allow_redirects=True)
            if r.status_code == 525:
                print(f"  525 SSL dari {url}, coba berikutnya...", flush=True)
                continue
            r.raise_for_status()
            if len(r.text) > 1000:
                html = r.text
                print(f"  OK — {len(html):,} chars dari {url}", flush=True)
                break
        except Exception as e:
            print(f"  GAGAL {url}: {e}", flush=True)

    if not html:
        print("  Semua URL gagal — skip paito-harian.", flush=True)
        return {}

    soup = BeautifulSoup(html, 'html.parser')
    found = {}

    # ── Strategy-0: scan .paito-line → nama di ancestor ──
    paito_lines_all = soup.find_all(class_='paito-line')
    if paito_lines_all:
        print(f"  Strategy-0: {len(paito_lines_all)} .paito-line ditemukan", flush=True)
        processed_parents = set()
        for line_el in paito_lines_all:
            result = _extract_4digit_from_paito_line(line_el)
            if not result:
                continue
            parent = line_el.parent
            for _ in range(6):
                if parent is None:
                    break
                heading_el = (
                    parent.find(['h1','h2','h3','h4','h5','h6','strong'],
                                class_=re.compile(r'(title|name|head|market|judul|label)', re.I))
                    or parent.find(['h1','h2','h3','h4','h5','h6','strong'])
                )
                if heading_el:
                    key = match_market(heading_el.get_text(strip=True))
                    if key and key not in found:
                        found[key] = result
                        print(f"  [{key.upper():6s}] {result}  (heading)", flush=True)
                        break
                pid = id(parent)
                if pid not in processed_parents:
                    processed_parents.add(pid)
                    key = match_market(parent.get_text(' ', strip=True))
                    if key and key not in found:
                        found[key] = result
                        print(f"  [{key.upper():6s}] {result}  (parent-text)", flush=True)
                        break
                parent = parent.parent
    else:
        print(f"  Strategy-0: tidak ada .paito-line di halaman ini ({len(html):,} chars)", flush=True)

    # ── Strategy-1: container+heading ──
    if len(found) < 10:
        print(f"  Strategy-1: {len(found)} → coba container+heading", flush=True)
        containers = soup.find_all(
            ['section', 'div', 'article', 'li'],
            class_=re.compile(r'(market|pasaran|paito|result|item|card|pool)', re.I)
        )
        for sec in containers:
            heading_el = (
                sec.find(['h1','h2','h3','h4','h5','strong'],
                         class_=re.compile(r'(title|name|head|market)', re.I))
                or sec.find(['h1','h2','h3','h4','h5','strong'])
            )
            if not heading_el:
                continue
            key = match_market(heading_el.get_text(strip=True))
            if not key or key in found:
                continue
            first_line = sec.find(class_='paito-line')
            if first_line:
                r = _extract_4digit_from_paito_line(first_line)
                if r:
                    found[key] = r
                    print(f"  [{key.upper():6s}] {r}  (strategy-1)", flush=True)
                    continue
            for tag in sec.find_all(['span','td','div','b','p']):
                t = tag.get_text(strip=True)
                if re.match(r'^\d{4}$', t) and not is_fake(t):
                    found[key] = t
                    print(f"  [{key.upper():6s}] {t}  (strategy-1 fallback)", flush=True)
                    break

    # ── Strategy-2: paito-row-item grouping ──
    if len(found) < 10:
        print(f"  Strategy-2: {len(found)} → coba paito-row-item", flush=True)
        row_map = {}
        for item in soup.find_all(class_='paito-row-item'):
            rid = id(item.parent)
            if rid not in row_map:
                row_map[rid] = {'date': None, 'result': None, 'name': None, 'el': item.parent}
            text = item.get_text(strip=True)
            digs = item.find_all(class_='paito-digit')
            if len(digs) >= 4:
                candidate = ''.join(d.get_text(strip=True) for d in digs[:4])
                if re.match(r'^\d{4}$', candidate) and not is_fake(candidate):
                    if row_map[rid]['result'] is None:
                        row_map[rid]['result'] = candidate
            if row_map[rid]['result'] is None and re.match(r'^\d{4}$', text) and not is_fake(text):
                row_map[rid]['result'] = text
            if row_map[rid]['name'] is None:
                key = match_market(text)
                if key:
                    row_map[rid]['name'] = key
        for rid, info in row_map.items():
            key = info.get('name') or match_market(
                info['el'].get_text(' ', strip=True) if info.get('el') else '')
            if key and key not in found and info.get('result'):
                found[key] = info['result']
                print(f"  [{key.upper():6s}] {info['result']}  (strategy-2)", flush=True)

    # ── Strategy-3: scan semua teks angka dan nama ──
    if len(found) < 10:
        print(f"  Strategy-3: {len(found)} → scan blok teks", flush=True)
        for el in soup.find_all(['div', 'section', 'article', 'li', 'tr']):
            txt = el.get_text(' ', strip=True)
            nums = re.findall(r'\b\d{4}\b', txt)
            valid_nums = [n for n in nums if not is_fake(n)]
            if not valid_nums:
                continue
            key = match_market(txt)
            if key and key not in found:
                found[key] = valid_nums[0]
                print(f"  [{key.upper():6s}] {valid_nums[0]}  (strategy-3)", flush=True)

    print(f"\n  [PAITO-HARIAN] Ditemukan: {len(found)}/{len(PASARAN)} pasaran", flush=True)
    return found


# ===== FETCH SATU PASARAN =====
def fetch_pasaran(key, path, name):
    urls_to_try = [
        (BASE + path,                  dict(HEADERS)),
        (f'https://{DIRECT_IP}{path}', {**HEADERS, 'Host': 'angkanet18.com'}),
    ]
    last_err = None

    for attempt_url, headers in urls_to_try:
        via = ' (via IP)' if DIRECT_IP in attempt_url else ''
        try:
            resp = requests.get(
                attempt_url, headers=headers,
                timeout=4, verify=False, allow_redirects=True,
            )
            if resp.status_code == 525:
                print(f"  [{key.upper():6s}] 525 SSL{via}", flush=True)
                last_err = '525 SSL'
                continue
            resp.raise_for_status()

            # ← SINGLE PARSE: result + rows sekaligus
            fetch_date, result, all_rows = extract_result_and_rows(resp.text)

            if result:
                if fetch_date is None:
                    fetch_date = list(TODAY_TUPLE)
                date_str = f"{fetch_date[0]:04d}-{fetch_date[1]:02d}-{fetch_date[2]:02d}"
                fd_t = tuple(fetch_date)
                if fd_t < TODAY_TUPLE:
                    # Data lama — result hari ini ditolak, tapi simpan rows sebagai history
                    stale_rows_info = f"  [{len(all_rows)}h]" if all_rows else ""
                    print(f"  [{key.upper():6s}] STALE {result} ({date_str}) — skip{stale_rows_info}", flush=True)
                    last_err = f'stale {date_str}'
                    # Kembalikan entry khusus: result='----' tapi bawa history rows-nya
                    if all_rows:
                        return {
                            'result':        '----',
                            'tgl':           TODAY,
                            'status':        'stale',
                            'updated':       NOW.strftime('%H:%M WIB'),
                            'name':          name,
                            'extra_history': all_rows,
                        }
                    continue
                print(f"  [{key.upper():6s}] OK {result}  ({name}){via}"
                      + (f"  [tgl:{date_str}]" if date_str else "")
                      + (f"  [{len(all_rows)}h]" if all_rows else ""), flush=True)
                return {
                    'result':        result,
                    'tgl':           TODAY,
                    'fetch_date':    list(fetch_date),
                    'status':        'sudah',
                    'updated':       NOW.strftime('%H:%M WIB'),
                    'name':          name,
                    'extra_history': all_rows,
                }
            else:
                print(f"  [{key.upper():6s}] WARN tidak ada angka{via}", flush=True)
                last_err = 'no result'
                continue

        except requests.RequestException as e:
            print(f"  [{key.upper():6s}] ERR {e}{via}", flush=True)
            last_err = str(e)
            continue
        except Exception as e:
            print(f"  [{key.upper():6s}] ERR {e}{via}", flush=True)
            last_err = str(e)
            continue

    if key in PASARAN_MALAM and NOW.hour < 23:
        print(f"  [{key.upper():6s}] Pasaran malam — wajar belum keluar", flush=True)
    else:
        print(f"  [{key.upper():6s}] GAGAL: {last_err}", flush=True)

    # Return None → main() akan JAGA data lama di result.json
    return None


# ===== HELPER SAVE =====
def _save_result(result_data, label=''):
    ok = [k for k in PASARAN if re.match(r'^\d{4}$', result_data.get(k, {}).get('result', ''))]
    result_data['_meta'] = {
        'updated': NOW.strftime('%Y-%m-%d %H:%M WIB'),
        'date': TODAY, 'today_str': TODAY_STR,
        'total': len(PASARAN), 'history_max': HISTORY_MAX,
        'elapsed_s': round(_elapsed(), 1),
    }
    with open('result.json', 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)
    print(f"  [SAVE{label}] result.json → {len(ok)}/{len(PASARAN)} valid  "
          f"(t={_elapsed():.1f}s)", flush=True)


# ===== MAIN =====
def main():
    print(f"\n{'='*60}", flush=True)
    print(f"fetch_all.py v5.0 — {NOW.strftime('%A, %d %B %Y %H:%M WIB')}", flush=True)
    print(f"Total pasaran: {len(PASARAN)}  |  History max: {HISTORY_MAX}", flush=True)
    print(f"{'='*60}\n", flush=True)

    try:
        with open('result.json', 'r', encoding='utf-8') as f:
            saved = json.load(f)
        print(f"Data lama: {len([k for k in saved if not k.startswith('_')])} pasaran\n", flush=True)
    except Exception:
        saved = {}
        print("Tidak ada data lama.\n", flush=True)

    result_data = {k: v for k, v in saved.items() if k in PASARAN or k.startswith('_')}

    # ── STEP 1: Paito-harian ──
    harian = fetch_paito_harian()

    needs_fetch = {}
    harian_entries = {}
    for key, (path, name) in PASARAN.items():
        if (key not in SKIP_PAITO_HARIAN
                and key in harian
                and re.match(r'^\d{4}$', harian[key])
                and not is_fake(harian[key])):
            harian_entries[key] = {
                'result': harian[key], 'tgl': TODAY,
                'fetch_date': list(TODAY_TUPLE), 'status': 'sudah',
                'updated': NOW.strftime('%H:%M WIB'), 'name': name,
            }
            print(f"  [{key.upper():6s}] {harian[key]}  ({name}) [paito-harian]", flush=True)
        else:
            if key in SKIP_PAITO_HARIAN and key in harian:
                print(f"  [{key.upper():6s}] skip paito-harian → fetch individual", flush=True)
            else:
                print(f"  [{key.upper():6s}] Fetch individual ← {BASE+path}", flush=True)
            needs_fetch[key] = (path, name)

    # ── STEP 2: Individual fetch paralel ──
    fetched_entries = {}
    MAX_WORKERS = 12

    if needs_fetch:
        print(f"\n  Fetching {len(needs_fetch)} pasaran (workers={MAX_WORKERS}, t={_elapsed():.1f}s)...", flush=True)

        def _fetch_one(item):
            k, (path, name) = item
            return k, fetch_pasaran(k, path, name)

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = {executor.submit(_fetch_one, item): item[0]
                       for item in needs_fetch.items()}
            for future in as_completed(futures):
                try:
                    k, entry = future.result()
                    fetched_entries[k] = entry
                except Exception as e:
                    k = futures[future]
                    print(f"  [{k.upper():6s}] THREAD ERR: {e}", flush=True)
                    fetched_entries[k] = {
                        'result': '----', 'tgl': TODAY, 'status': 'belum',
                        'updated': NOW.strftime('%H:%M WIB'), 'name': needs_fetch[k][1],
                    }

    print(f"\n  Fetch selesai t={_elapsed():.1f}s", flush=True)

    # ── Gabung dan proses history ──
    all_entries = {**harian_entries, **fetched_entries}

    for key, (path, name) in PASARAN.items():
        entry = all_entries.get(key)
        # None = fetch gagal/stale → JAGA data lama di result_data
        if entry is None:
            if key in result_data:
                print(f"  [{key.upper():6s}] KEEP data lama: {result_data[key].get('result','----')} ({result_data[key].get('tgl','-')})", flush=True)
            continue
        old = result_data.get(key, {})
        if entry['result'] != '----':
            old_fd = old.get('fetch_date')
            new_fd = entry.get('fetch_date')
            old_res = old.get('result', '')
            should_overwrite = True
            if new_fd is not None:
                new_fd_t = tuple(new_fd)
                if old_fd is not None:
                    if new_fd_t < tuple(old_fd):
                        should_overwrite = False
                else:
                    if new_fd_t < TODAY_TUPLE and not is_fake(old_res):
                        should_overwrite = False
            if should_overwrite:
                entry_date = (f"{new_fd[0]:04d}-{new_fd[1]:02d}-{new_fd[2]:02d}"
                              if new_fd else TODAY_STR)
                base_history = update_history(old, entry['result'], entry_date)
                extra = entry.pop('extra_history', [])
                if extra:
                    base_history = merge_rows_into_history(base_history, extra)
                entry['history'] = base_history
                result_data[key] = entry
            else:
                result_data[key] = old
        elif key not in result_data:
            # Entry baru, tapi result='----' — simpan minimal + history-nya
            extra = entry.pop('extra_history', [])
            entry['history'] = extra[:HISTORY_MAX] if extra else []
            result_data[key] = entry
        else:
            # Key sudah ada — jaga data lama, tapi merge extra_history dari stale fetch
            extra = entry.pop('extra_history', [])
            old_result = result_data[key].get('result', '')
            if extra:
                merged_hist = merge_rows_into_history(old.get('history', []), extra)
                result_data[key]['history'] = merged_hist
                print(f"  [{key.upper():6s}] +history dari stale: {len(merged_hist)} entry", flush=True)
            if is_fake(old_result):
                entry['history'] = result_data[key].get('history', [])
                result_data[key] = entry

    # ── SAVE #1: sebelum backfill — data aman ──
    _save_result(result_data, ' #1')

    # ── STEP 3: Backfill ──
    BACKFILL_THRESHOLD = HISTORY_MAX
    BACKFILL_LIMIT = 5   # max 5 per run — akumulasi tiap hari
    tl = _time_left(270)

    # Hitung berapa pasaran yang sudah punya history
    has_history = [k for k in PASARAN if len(result_data.get(k, {}).get('history', [])) >= 3]
    is_fresh_start = len(has_history) < 10  # fresh start jika < 10 pasaran punya history

    if is_fresh_start:
        print(f"\n[BACKFILL] Skip — fresh start ({len(has_history)} pasaran punya history). "
              f"History akan akumulasi tiap run.", flush=True)
        needs_backfill = []
    elif tl < 90:
        print(f"\n[BACKFILL] Skip — sisa {tl:.0f}s < 90s", flush=True)
        needs_backfill = []
    else:
        needs_backfill = [
            (k, PASARAN[k]) for k in PASARAN
            if len(result_data.get(k, {}).get('history', [])) < BACKFILL_THRESHOLD
            and result_data.get(k, {}).get('result', '----') != '----'
        ]

    if needs_backfill:
        batch = needs_backfill[:BACKFILL_LIMIT]
        print(f"\n[BACKFILL] {len(needs_backfill)} perlu backfill → proses {len(batch)} "
              f"(sisa {tl:.0f}s)", flush=True)

        def _backfill_one(item):
            key, (path, name) = item
            cur_hist = result_data[key].get('history', [])
            print(f"  [BF {key.upper():6s}] fetch (hist:{len(cur_hist)})", flush=True)
            try:
                r = requests.get(BASE + path, headers=dict(HEADERS),
                                 timeout=4, verify=False, allow_redirects=True)
                r.raise_for_status()
                if len(r.text) < 500:
                    return key, None
                _, _, rows = extract_result_and_rows(r.text)
                if rows:
                    new_hist = merge_rows_into_history(cur_hist, rows)
                    print(f"  [BF {key.upper():6s}] {len(new_hist)} entry (+{len(new_hist)-len(cur_hist)})", flush=True)
                    return key, new_hist
            except Exception as e:
                print(f"  [BF {key.upper():6s}] ERR {e}", flush=True)
            return key, None

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(_backfill_one, item) for item in batch]
            for future in as_completed(futures):
                try:
                    key, new_hist = future.result()
                    if new_hist is not None:
                        result_data[key]['history'] = new_hist
                except Exception as e:
                    print(f"  [BF] ERR {e}", flush=True)

    # ── Manual override ──
    for ov_key, ov_result in MANUAL_OVERRIDE.items():
        if ov_key in result_data:
            result_data[ov_key]['result'] = ov_result
            result_data[ov_key]['status'] = 'sudah'
            result_data[ov_key]['fetch_date'] = list(TODAY_TUPLE)
            result_data[ov_key]['updated'] = NOW.strftime('%H:%M WIB') + ' [MANUAL]'
            result_data[ov_key]['history'] = update_history(
                result_data[ov_key], ov_result, TODAY_STR)

    # ── SAVE #2: final ──
    _save_result(result_data, ' #2 FINAL')

    ok = [k for k in PASARAN if re.match(r'^\d{4}$', result_data.get(k, {}).get('result', ''))]
    hist_ok = [k for k in PASARAN if result_data.get(k, {}).get('history')]
    avg = (sum(len(result_data[k].get('history', [])) for k in hist_ok) / len(hist_ok)) if hist_ok else 0
    print(f"\n{'='*60}", flush=True)
    print(f"SELESAI  t={_elapsed():.1f}s", flush=True)
    print(f"Valid    : {len(ok)}/{len(PASARAN)}", flush=True)
    print(f"History  : {len(hist_ok)} pasaran  (rata {avg:.1f} entry)", flush=True)
    print(f"{'='*60}\n", flush=True)


if __name__ == '__main__':
    main()
