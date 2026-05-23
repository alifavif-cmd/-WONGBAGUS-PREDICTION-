"""
fetch_all.py — Fetch 65 pasaran togel dari angkanet.com
Simpan ke result.json, dibaca langsung oleh index.html
"""

import requests
import json
import re
import time
import urllib3
urllib3.disable_warnings()
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

# ===== TIMEZONE =====
WIB = timezone(timedelta(hours=7))
NOW = datetime.now(WIB)
TODAY = NOW.strftime('%d/%m')

BASE      = 'https://angkanet18.com'
DIRECT_IP = '159.65.133.131'

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

TODAY_TUPLE = (NOW.year, NOW.month, NOW.day)

# ===== MANUAL OVERRIDE =====
# Isi kalau angkanet fetch data SALAH/stale untuk hari ini.
# Format: 'key': 'result4digit'  — hapus setelah hari berganti!
MANUAL_OVERRIDE = {
    # 'sdl': '1864',   # 20-05-2026: angkanet stuck di 2572 (data 19-05)
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

def is_fake(result):
    if not result or not re.match(r'^\d{4}$', result):
        return True
    if is_year(result):
        return True
    return any(re.match(p, result) for p in FAKE_PATTERNS)


# ===== EKSTRAK RESULT DARI HTML =====
def extract_result(html):
    """
    Logika:
    - Group semua paito-row-item berdasarkan parent element (= 1 baris data).
    - Tiap grup: cari apakah ada tanggal (dd-mm-yyyy) dan angka 4-digit valid.
    - Kumpulkan semua baris yang punya keduanya → sort by tanggal → ambil TERBARU.
    - Tidak tebak urutan DOM sama sekali, jadi aman untuk tabel ascending maupun descending.
    """
    if not html or len(html) < 200:
        return None, None

    soup = BeautifulSoup(html, 'html.parser')
    all_items = soup.find_all(class_='paito-row-item')

    if not all_items:
        # Halaman struktur beda — ambil 4-digit valid terakhir di halaman
        last_valid = None
        for tag in soup.find_all(['span', 'td']):
            t = tag.get_text(strip=True)
            if re.match(r'^\d{4}$', t) and not is_fake(t):
                last_valid = t
        return None, last_valid  # ← tidak ada info tanggal

    # --- Group per parent row ---
    # Support dd-mm-yyyy | dd/mm/yyyy | yyyy-mm-dd | yyyy/mm/dd
    date_pat = re.compile(
        r'^(?:(\d{2})[/-](\d{2})[/-](\d{4})|(\d{4})[/-](\d{2})[/-](\d{2}))$'
    )
    row_map  = {}

    for item in all_items:
        row_el = item.parent
        row_id = id(row_el)
        if row_id not in row_map:
            row_map[row_id] = {'date': None, 'result': None}
        text = item.get_text(strip=True)

        # Tangkap tanggal jika belum
        if row_map[row_id]['date'] is None:
            m = date_pat.match(text)
            if m:
                if m.group(1):  # dd-mm-yyyy atau dd/mm/yyyy
                    d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
                else:           # yyyy-mm-dd atau yyyy/mm/dd
                    y, mo, d = int(m.group(4)), int(m.group(5)), int(m.group(6))
                row_map[row_id]['date'] = (y, mo, d)

        # Tangkap result 4-digit pertama yang valid jika belum
        if row_map[row_id]['result'] is None:
            if re.match(r'^\d{4}$', text) and not is_fake(text):
                row_map[row_id]['result'] = text

    # --- Kumpulkan baris yang punya tanggal DAN result valid ---
    valid_rows = [
        (r['date'], r['result'])
        for r in row_map.values()
        if r['date'] is not None and r['result'] is not None
    ]

    if valid_rows:
        # Sort by tanggal (tuple yyyy, mm, dd) → ambil paling baru
        valid_rows.sort(key=lambda x: x[0])
        latest_date, latest_result = valid_rows[-1]
        return latest_date, latest_result  # ← return date + result

    # --- Fallback: tidak ada baris bertanggal, ambil 4-digit valid terakhir ---
    last_valid = None
    for tag in soup.find_all(['span', 'td']):
        t = tag.get_text(strip=True)
        if re.match(r'^\d{4}$', t) and not is_fake(t):
            last_valid = t
    return None, last_valid  # ← tidak ada info tanggal


# ===== PAITO HARIAN — FETCH SEMUA SEKALIGUS (1 REQUEST) =====
PAITO_HARIAN_URL = f'{BASE}/paito-harian/'

# Mapping keyword → key pasaran (urut: paling spesifik duluan)
KEYWORD_MAP = [
    ('hongkong pool',          'hk'),
    ('hk pools',               'hk'),
    ('hk lotto',               'hkl'),
    ('hklotto',                'hkl'),
    ('singapore',              'sgp'),
    ('sydney pools',           'sdy'),
    ('sydney pool',            'sdy'),
    ('sydney lotto',           'sdl'),
    ('sdlotto',                'sdl'),
    ('magnum cambodia',        'kam'),
    ('kamboja',                'kam'),
    ('cambodia',               'kam'),
    ('bullseye',               'bull'),
    ('china pool',             'chn'),
    ('chinapool',              'chn'),
    ('japan',                  'jpn'),
    ('taiwan',                 'twn'),
    ('pcso',                   'pcso'),
    ('toto macau 1',           'mac1'),
    ('macau 13',               'mac1'),
    ('toto macau 2',           'mac2'),
    ('macau 16',               'mac2'),
    ('toto macau 3',           'mac3'),
    ('macau 19',               'mac3'),
    ('toto macau 4',           'mac4'),
    ('macau 22',               'mac4'),
    ('toto macau 5',           'mac5'),
    ('macau 00',               'mac5'),
    ('toto macau 6',           'mac6'),
    ('macau 23',               'mac6'),
    ('morocco quatro 03',      'mrq3'),
    ('morocco 03',             'mrq3'),
    ('morocco quatro 18',      'mrq18'),
    ('morocco 18',             'mrq18'),
    ('morocco quatro 21',      'mrq21'),
    ('morocco 21',             'mrq21'),
    ('morocco quatro 23',      'mrq23'),
    ('morocco 23',             'mrq23'),
    ('germany',                'ger'),
    ('oregon 04',              'or4'),
    ('oregon 07',              'or7'),
    ('oregon 10',              'or10'),
    ('oregon 13',              'or13'),
    ('north carolina day',     'ncd'),
    ('nc day',                 'ncd'),
    ('north carolina evening', 'nce'),
    ('nc evening',             'nce'),
    ('georgia midday',         'geom'),
    ('georgia mid',            'geom'),
    ('georgia evening',        'geoe'),
    ('georgia eve',            'geoe'),
    ('georgia night',          'geon'),
    ('texas morning',          'txmr'),
    ('texas day',              'txd'),
    ('texas evening',          'txe'),
    ('texas night',            'txn'),
    ('new york midday',        'nyd'),
    ('new york evening',       'nye'),
    ('new jersey midday',      'njm'),
    ('nj midday',              'njm'),
    ('new jersey evening',     'nje'),
    ('nj evening',             'nje'),
    ('florida midday',         'flm'),
    ('florida evening',        'fle'),
    ('illinois midday',        'ilm'),
    ('illinois evening',       'ile'),
    ('indiana midday',         'indm'),
    ('indiana evening',        'inde'),
    ('kentucky midday',        'kym'),
    ('kentucky evening',       'kye'),
    ('maryland midday',        'mdm'),
    ('maryland evening',       'mde'),
    ('michigan midday',        'mim'),
    ('michigan evening',       'mie'),
    ('missouri midday',        'mom'),
    ('missouri evening',       'moe'),
    ('washington dc midday',   'wdm'),
    ('wdc midday',             'wdm'),
    ('washington dc evening',  'wde'),
    ('wdc evening',            'wde'),
    ('connecticut day',        'ctd'),
    ('connecticut night',      'ctn'),
    ('virginia day',           'vad'),
    ('virginia night',         'van'),
    ('tennesse midday',        'tnm'),
    ('tennessee midday',       'tnm'),
    ('tennesse evening',       'tne'),
    ('tennessee evening',      'tne'),
    ('tennesse morning',       'tnmr'),
    ('tennessee morning',      'tnmr'),
    ('california',             'cal'),
    ('wisconsin evening',      'wie'),
]


def match_market(text):
    """Cocokkan teks ke key pasaran (case-insensitive)."""
    tl = text.lower()
    for kw, key in KEYWORD_MAP:
        if kw in tl:
            return key
    return None


def fetch_paito_harian():
    """
    Fetch SEMUA result dari 1 halaman paito-harian.
    Jauh lebih cepat dari 65 request individual.
    Return: dict {key: result_4digit}
    """
    print(f"\n{'='*60}")
    print(f"[PAITO-HARIAN] {PAITO_HARIAN_URL}")
    print(f"{'='*60}")

    html = None
    for url, hdrs in [
        (PAITO_HARIAN_URL,                       dict(HEADERS)),
        (f'https://{DIRECT_IP}/paito-harian/',   {**HEADERS, 'Host': 'angkanet18.com'}),
    ]:
        try:
            time.sleep(0.5)
            r = requests.get(url, headers=hdrs, timeout=20, verify=False, allow_redirects=True)
            if r.status_code == 525:
                print(f"  525 SSL dari {url}, coba berikutnya...")
                continue
            r.raise_for_status()
            if len(r.text) > 1000:
                html = r.text
                print(f"  OK — {len(html):,} chars dari {url}")
                break
        except Exception as e:
            print(f"  GAGAL {url}: {e}")

    if not html:
        print("  Semua URL gagal — skip paito-harian.")
        return {}

    soup = BeautifulSoup(html, 'html.parser')
    found = {}

    # ── Strategy 1: Section/div per pasaran dengan heading ──
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
        for tag in sec.find_all(['span','td','div','b','p']):
            t = tag.get_text(strip=True)
            if re.match(r'^\d{4}$', t) and not is_fake(t):
                found[key] = t
                print(f"  [{key.upper():6s}] {t}  (strategy-1 heading)")
                break

    # ── Strategy 2: paito-row-item grouped by parent ──
    if len(found) < 10:
        print(f"  Strategy-1: {len(found)} → coba strategy-2 (paito-row-item)")
        row_map = {}
        for item in soup.find_all(class_='paito-row-item'):
            rid = id(item.parent)
            if rid not in row_map:
                row_map[rid] = {'texts': [], 'result': None}
            t = item.get_text(strip=True)
            row_map[rid]['texts'].append(t)
            if row_map[rid]['result'] is None and re.match(r'^\d{4}$', t) and not is_fake(t):
                row_map[rid]['result'] = t
        for info in row_map.values():
            if not info['result']:
                continue
            key = match_market(' '.join(info['texts']))
            if key and key not in found:
                found[key] = info['result']
                print(f"  [{key.upper():6s}] {info['result']}  (strategy-2 row-item)")

    # ── Strategy 3: scan <tr>/<li> teks pendek dengan konteks parent ──
    if len(found) < 5:
        print(f"  Strategy-2: {len(found)} → coba strategy-3 (scan blok)")
        for block in soup.find_all(['tr','li'], limit=3000):
            t = block.get_text(strip=True)
            if not (re.match(r'^\d{4}$', t) and not is_fake(t)):
                continue
            parent_txt = block.parent.get_text(' ', strip=True) if block.parent else ''
            key = match_market(parent_txt)
            if key and key not in found:
                found[key] = t
                print(f"  [{key.upper():6s}] {t}  (strategy-3 scan)")

    print(f"\n  [PAITO-HARIAN] Ditemukan: {len(found)}/{len(PASARAN)} pasaran\n")
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
            time.sleep(0.5)
            resp = requests.get(
                attempt_url, headers=headers,
                timeout=15, verify=False, allow_redirects=True,
            )

            if resp.status_code == 525:
                print(f"  [{key.upper():6s}] 525 SSL Error{via}, coba fallback...")
                last_err = '525 SSL Error'
                continue

            resp.raise_for_status()
            fetch_date, result = extract_result(resp.text)

            if result:
                # === FIX: fetch_date null → fallback hari ini ===
                # Kalau HTML tidak punya tanggal eksplisit, anggap data milik hari ini
                # supaya stale-check bisa bekerja
                if fetch_date is None:
                    fetch_date = list(TODAY_TUPLE)

                date_str = (
                    f"{fetch_date[0]:04d}-{fetch_date[1]:02d}-{fetch_date[2]:02d}"
                    if fetch_date else None
                )

                # === CEK STALE DATA ===
                # Kalau data dari website adalah milik HARI KEMARIN (atau lebih lama),
                # jangan simpan — anggap belum keluar hari ini.
                if fetch_date and tuple(fetch_date) < TODAY_TUPLE:
                    print(f"  [{key.upper():6s}] STALE {result} dari {date_str} "
                          f"(bukan hari ini {TODAY_TUPLE}) → anggap belum keluar")
                    last_err = f'stale data dari {date_str}'
                    continue   # coba URL fallback; kalau semua stale → return ----

                print(f"  [{key.upper():6s}] OK {result}  ({name}){via}"
                      + (f"  [tgl: {date_str}]" if date_str else ""))
                return {
                    'result':     result,
                    'tgl':        TODAY,
                    'fetch_date': list(fetch_date),   # ← selalu list, tidak pernah null
                    'status':     'sudah',
                    'updated':    NOW.strftime('%H:%M WIB'),
                    'name':       name,
                }
            else:
                print(f"  [{key.upper():6s}] WARN angka tidak ketemu{via}  ({name})")
                last_err = 'angka tidak ketemu'
                continue

        except requests.RequestException as e:
            print(f"  [{key.upper():6s}] ERR {e}{via}  ({name})")
            last_err = str(e)
            continue
        except Exception as e:
            print(f"  [{key.upper():6s}] ERR {e}{via}  ({name})")
            last_err = str(e)
            continue

    if key in PASARAN_MALAM and NOW.hour < 23:
        print(f"  [{key.upper():6s}] INFO: Pasaran malam (jam {NOW.hour:02d}:xx WIB) — wajar belum keluar")
    else:
        print(f"  [{key.upper():6s}] FINAL GAGAL: {last_err}")

    return {
        'result':  '----',
        'tgl':     TODAY,
        'status':  'belum',
        'updated': NOW.strftime('%H:%M WIB'),
        'name':    name,
    }


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

    # Bersihkan key obsolete — hanya pertahankan key yang ada di PASARAN + _meta
    result_data = {k: v for k, v in saved.items() if k in PASARAN or k.startswith('_')}

    # ── STEP 1: Fetch paito-harian dulu (1 request untuk semua pasaran) ──
    harian = fetch_paito_harian()

    for key, (path, name) in PASARAN.items():
        # Gunakan hasil paito-harian kalau valid, skip individual fetch
        if key in harian and re.match(r'^\d{4}$', harian[key]) and not is_fake(harian[key]):
            entry = {
                'result':     harian[key],
                'tgl':        TODAY,
                'fetch_date': list(TODAY_TUPLE),
                'status':     'sudah',
                'updated':    NOW.strftime('%H:%M WIB'),
                'name':       name,
            }
            print(f"  [{key.upper():6s}] {harian[key]}  ({name}) [paito-harian]")
        else:
            # Fallback: fetch halaman individual
            if key in harian:
                print(f"  [{key.upper():6s}] Tidak valid dari paito-harian, fetch individual...")
            else:
                print(f"Fetching {key.upper()} <- {BASE+path}")
            entry = fetch_pasaran(key, path, name)

        if entry['result'] != '----':
            old     = result_data.get(key, {})
            old_fd  = old.get('fetch_date')    # [y,m,d] atau None
            new_fd  = entry.get('fetch_date')  # [y,m,d] atau None
            today_t = (NOW.year, NOW.month, NOW.day)
            old_res = old.get('result', '')

            should_overwrite = True

            if new_fd is not None:
                new_fd_t = tuple(new_fd)
                if old_fd is not None:
                    # Keduanya punya tanggal → bandingkan langsung
                    if new_fd_t < tuple(old_fd):
                        should_overwrite = False
                else:
                    # Old TIDAK punya fetch_date (script versi lama)
                    # Kalau fetch dapat data KEMARIN dan old masih valid → jangan overwrite
                    if new_fd_t < today_t and not is_fake(old_res):
                        should_overwrite = False

            if should_overwrite:
                result_data[key] = entry
            else:
                ref = ('saved ' + str(old_fd)) if old_fd else ('TODAY ' + str(list(today_t)))
                print(f"  [{key.upper():6s}] SKIP overwrite: "
                      f"fetch {new_fd} < {ref}, "
                      f"pakai data lama: {old_res}")
        elif key not in result_data:
            result_data[key] = entry
        else:
            old_result = result_data[key].get('result', '')
            if is_fake(old_result):
                print(f"  [{key.upper():6s}] Data lama '{old_result}' INVALID, reset ke ----")
                result_data[key] = entry
            else:
                print(f"  [{key.upper():6s}] Pakai data lama: {old_result}")

    # ===== TERAPKAN MANUAL OVERRIDE =====
    for ov_key, ov_result in MANUAL_OVERRIDE.items():
        if ov_key in result_data:
            old_val = result_data[ov_key].get('result', '----')
            print(f"  [{ov_key.upper():6s}] MANUAL OVERRIDE: {old_val} → {ov_result}")
            result_data[ov_key]['result']     = ov_result
            result_data[ov_key]['status']     = 'sudah'
            result_data[ov_key]['fetch_date'] = list(TODAY_TUPLE)
            result_data[ov_key]['updated']    = NOW.strftime('%H:%M WIB') + ' [MANUAL]'

    result_data['_meta'] = {
        'updated': NOW.strftime('%Y-%m-%d %H:%M WIB'),
        'date':    TODAY,
        'total':   len(PASARAN),
    }

    with open('result.json', 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)

    ok = [k for k in PASARAN
          if re.match(r'^\d{4}$', result_data.get(k, {}).get('result', ''))]
    print(f"\n{'='*60}")
    print(f"result.json tersimpan | Valid: {len(ok)} | Belum: {len(PASARAN)-len(ok)}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
