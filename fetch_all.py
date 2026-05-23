"""
fetch_all.py — Ambil semua result dari SATU halaman paito-harian
https://angkanet18.com/paito-harian/
Jauh lebih efisien: 1 request → semua pasaran, bukan 65 request terpisah.
"""

import requests
import json
import re
import time
import urllib3
urllib3.disable_warnings()
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup

# ───────────────────────────────────────────────
# TIMEZONE & CONFIG
# ───────────────────────────────────────────────
WIB       = timezone(timedelta(hours=7))
NOW       = datetime.now(WIB)
TODAY     = NOW.strftime('%d/%m')
TODAY_ISO = NOW.strftime('%Y-%m-%d')
TODAY_T   = (NOW.year, NOW.month, NOW.day)

BASE        = 'https://angkanet18.com'
DIRECT_IP   = '159.65.133.131'
PAITO_URL   = BASE + '/paito-harian/'
PAITO_URL_IP= f'https://{DIRECT_IP}/paito-harian/'

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8',
}

# ───────────────────────────────────────────────
# MAPPING: nama di HTML  →  key result.json
# Lowercase, strip, fleksibel
# ───────────────────────────────────────────────
NAME_MAP = {
    # Asia
    'hongkong pools':         'hk',
    'hongkong':               'hk',
    'hk pools':               'hk',
    'hongkong lotto':         'hkl',
    'hk lotto':               'hkl',
    'hklotto':                'hkl',
    'singapore':              'sgp',
    'sgp':                    'sgp',
    'singapore pools':        'sgp',
    'sydney pools':           'sdy',
    'sydney lotto':           'sdl',
    'sdlotto':                'sdl',
    'sd lotto':               'sdl',
    'kamboja':                'kam',
    'cambodia':               'kam',
    'magnum cambodia':        'kam',
    'bullseye':               'bull',
    'bullseye nz':            'bull',
    'china pools':            'chn',
    'chinapools':             'chn',
    'japan':                  'jpn',
    'taiwan':                 'twn',
    'pcso':                   'pcso',
    # Macau
    'toto macau 13':          'mac1',
    'toto macau 1':           'mac1',
    'macau 13:10':            'mac1',
    'macau 13.10':            'mac1',
    'toto macau 16':          'mac2',
    'toto macau 2':           'mac2',
    'macau 16:10':            'mac2',
    'toto macau 19':          'mac3',
    'toto macau 3':           'mac3',
    'macau 19:10':            'mac3',
    'toto macau 22':          'mac4',
    'toto macau 4':           'mac4',
    'macau 22:10':            'mac4',
    'toto macau 00':          'mac5',
    'toto macau 5':           'mac5',
    'toto macau 23':          'mac6',
    'toto macau 6':           'mac6',
    'macau 23:10':            'mac6',
    # Morocco
    'morocco 03':             'mrq3',
    'morocco quatro 03':      'mrq3',
    'morocco 18':             'mrq18',
    'morocco quatro 18':      'mrq18',
    'morocco 21':             'mrq21',
    'morocco quatro 21':      'mrq21',
    'morocco 23':             'mrq23',
    'morocco quatro 23':      'mrq23',
    'morocco quatro 23:59':   'mrq23',
    # Germany
    'germany plus5':          'ger',
    'germany':                'ger',
    # Oregon
    'oregon 04':              'or4',
    'oregon 04:00':           'or4',
    'oregon 07':              'or7',
    'oregon 07:00':           'or7',
    'oregon 10':              'or10',
    'oregon 10:00':           'or10',
    'oregon 13':              'or13',
    'oregon 13:00':           'or13',
    # North Carolina
    'north carolina day':     'ncd',
    'nc day':                 'ncd',
    'north carolina evening': 'nce',
    'nc evening':             'nce',
    # Georgia
    'georgia midday':         'geom',
    'georgia mid':            'geom',
    'georgia evening':        'geoe',
    'georgia eve':            'geoe',
    'georgia night':          'geon',
    # Texas
    'texas day':              'txd',
    'texas morning':          'txmr',
    'texas evening':          'txe',
    'texas night':            'txn',
    # New York
    'new york midday':        'nyd',
    'ny midday':              'nyd',
    'new york evening':       'nye',
    'ny evening':             'nye',
    # New Jersey
    'new jersey midday':      'njm',
    'nj midday':              'njm',
    'new jersey evening':     'nje',
    'nj evening':             'nje',
    # Florida
    'florida midday':         'flm',
    'florida mid':            'flm',
    'florida evening':        'fle',
    'florida eve':            'fle',
    # Illinois
    'illinois midday':        'ilm',
    'illinois mid':           'ilm',
    'illinois evening':       'ile',
    'illinois eve':           'ile',
    # Indiana
    'indiana midday':         'indm',
    'indiana mid':            'indm',
    'indiana evening':        'inde',
    'indiana eve':            'inde',
    # Kentucky
    'kentucky midday':        'kym',
    'kentucky mid':           'kym',
    'kentucky evening':       'kye',
    'kentucky eve':           'kye',
    # Maryland
    'maryland midday':        'mdm',
    'maryland mid':           'mdm',
    'maryland evening':       'mde',
    'maryland eve':           'mde',
    # Michigan
    'michigan midday':        'mim',
    'michigan mid':           'mim',
    'michigan evening':       'mie',
    'michigan eve':           'mie',
    # Missouri
    'missouri midday':        'mom',
    'missouri mid':           'mom',
    'missouri evening':       'moe',
    'missouri eve':           'moe',
    # Washington DC
    'washington dc midday':   'wdm',
    'wdc midday':             'wdm',
    'wdc mid':                'wdm',
    'washington dc evening':  'wde',
    'wdc evening':            'wde',
    'wdc eve':                'wde',
    # Connecticut
    'connecticut day':        'ctd',
    'conn day':               'ctd',
    'connecticut night':      'ctn',
    'conn night':             'ctn',
    # Virginia
    'virginia day':           'vad',
    'virginia night':         'van',
    # Tennessee
    'tennessee midday':       'tnm',
    'tennesse midday':        'tnm',
    'tenn midday':            'tnm',
    'tennessee evening':      'tne',
    'tennesse evening':       'tne',
    'tenn evening':           'tne',
    'tennessee morning':      'tnmr',
    'tennesse morning':       'tnmr',
    'tenn morning':           'tnmr',
    # California, Wisconsin
    'california':             'cal',
    'wisconsin evening':      'wie',
    'wisconsin eve':          'wie',
    'wisconsin midday':       'wim',
    'wisconsin mid':          'wim',
}

# Human-readable names untuk result.json
PASARAN_NAMES = {
    'hk':'Hongkong Pools','hkl':'Hongkong Lotto','sgp':'Singapore',
    'sdy':'Sydney Pools','sdl':'Sydney Lotto','kam':'Kamboja',
    'bull':'Bullseye NZ','chn':'China Pools','jpn':'Japan','twn':'Taiwan','pcso':'PCSO',
    'mac1':'Toto Macau 13','mac2':'Toto Macau 16','mac3':'Toto Macau 19',
    'mac4':'Toto Macau 22','mac5':'Toto Macau 00','mac6':'Toto Macau 23',
    'mrq3':'Morocco 03:00','mrq18':'Morocco 18:00','mrq21':'Morocco 21:00','mrq23':'Morocco 23:59',
    'ger':'Germany Plus5',
    'or4':'Oregon 04:00','or7':'Oregon 07:00','or10':'Oregon 10:00','or13':'Oregon 13:00',
    'ncd':'NC Day','nce':'NC Evening',
    'geom':'Georgia Midday','geoe':'Georgia Evening','geon':'Georgia Night',
    'txd':'Texas Day','txmr':'Texas Morning','txe':'Texas Evening','txn':'Texas Night',
    'nyd':'New York Midday','nye':'New York Evening',
    'njm':'NJ Midday','nje':'NJ Evening',
    'flm':'Florida Midday','fle':'Florida Evening',
    'ilm':'Illinois Midday','ile':'Illinois Evening',
    'indm':'Indiana Midday','inde':'Indiana Evening',
    'kym':'Kentucky Midday','kye':'Kentucky Evening',
    'mdm':'Maryland Midday','mde':'Maryland Evening',
    'mim':'Michigan Midday','mie':'Michigan Evening',
    'mom':'Missouri Midday','moe':'Missouri Evening',
    'wdm':'WDC Midday','wde':'WDC Evening',
    'ctd':'Connecticut Day','ctn':'Connecticut Night',
    'vad':'Virginia Day','van':'Virginia Night',
    'tnm':'Tennessee Midday','tne':'Tennessee Evening','tnmr':'Tennessee Morning',
    'cal':'California','wie':'Wisconsin Evening','wim':'Wisconsin Midday',
}

ALL_KEYS = set(PASARAN_NAMES.keys())

# ───────────────────────────────────────────────
# HELPER
# ───────────────────────────────────────────────
FAKE_PATTERNS = [
    r'^1234$',r'^2345$',r'^3456$',r'^4567$',r'^5678$',
    r'^6789$',r'^7890$',r'^8901$',r'^9012$',r'^0123$',
    r'^(\d)\1{3}$',
]

def is_fake(result):
    if not result or not re.match(r'^\d{4}$', result):
        return True
    try:
        n = int(result)
        if 1800 <= n <= 2100:
            return True
    except Exception:
        pass
    return any(re.match(p, result) for p in FAKE_PATTERNS)

def normalize_name(raw):
    """Lowercase, collapse whitespace, strip."""
    return re.sub(r'\s+', ' ', raw.lower().strip())

def match_key(raw_name):
    """Cari key dari raw_name. Return None jika tidak ketemu."""
    n = normalize_name(raw_name)
    if n in NAME_MAP:
        return NAME_MAP[n]
    # Partial match — cari substring terpanjang
    best = None
    best_len = 0
    for k, v in NAME_MAP.items():
        if k in n and len(k) > best_len:
            best, best_len = v, len(k)
    return best

# ───────────────────────────────────────────────
# FETCH PAITO HARIAN (1 REQUEST)
# ───────────────────────────────────────────────
def fetch_paito_harian():
    """
    Fetch halaman /paito-harian/ dan parse semua result.
    Return: dict {key: entry_dict}
    """
    urls_to_try = [
        (PAITO_URL,    dict(HEADERS)),
        (PAITO_URL_IP, {**HEADERS, 'Host': 'angkanet18.com'}),
    ]

    html = None
    for url, hdrs in urls_to_try:
        try:
            print(f"  Fetch: {url}")
            r = requests.get(url, headers=hdrs, timeout=20,
                             verify=False, allow_redirects=True)
            if r.status_code == 525:
                print(f"  525 SSL Error — coba fallback IP...")
                continue
            r.raise_for_status()
            if len(r.text) > 1000:
                html = r.text
                print(f"  HTML didapat: {len(html):,} bytes")
                break
        except Exception as e:
            print(f"  ERR fetch: {e}")
            continue

    if not html:
        print("  GAGAL: tidak bisa fetch /paito-harian/")
        return {}

    return parse_paito_harian(html)


def parse_paito_harian(html):
    """
    Multi-strategi parser untuk /paito-harian/:
    Strategi A — paito-row-item (struktur utama angkanet)
    Strategi B — tabel HTML biasa
    Strategi C — brute-force: pasangan (nama, 4D) berdekatan
    """
    soup = BeautifulSoup(html, 'html.parser')
    result = {}

    # ── Strategi A: paito-row-item ──────────────────
    rows = soup.find_all(class_=re.compile(r'paito-row\b'))
    if not rows:
        rows = soup.find_all(class_=re.compile(r'paito.*row'))

    if rows:
        print(f"  Strategi A: {len(rows)} paito-row ditemukan")
        for row in rows:
            items = row.find_all(class_=re.compile(r'paito-row-item'))
            texts = [i.get_text(strip=True) for i in items]
            if not texts:
                texts = [c.get_text(strip=True) for c in row.children
                         if hasattr(c, 'get_text')]

            # Dari texts, cari nama pasaran dan angka 4D
            row_name = None
            row_result = None
            for t in texts:
                if re.match(r'^\d{4}$', t) and not is_fake(t) and row_result is None:
                    row_result = t
                elif len(t) > 3 and not re.match(r'^[\d/\-: ]+$', t) and row_name is None:
                    row_name = t

            if row_name and row_result:
                key = match_key(row_name)
                if key and key not in result:
                    result[key] = _make_entry(row_result, key)
                    print(f"    [{key.upper():6s}] {row_result}  ← \"{row_name}\"")

    # ── Strategi B: tabel ───────────────────────────
    if len(result) < 5:
        print(f"  Strategi B: cari tabel HTML")
        for table in soup.find_all('table'):
            for tr in table.find_all('tr'):
                tds = [td.get_text(strip=True) for td in tr.find_all(['td','th'])]
                if len(tds) < 2:
                    continue
                row_name, row_result = None, None
                for t in tds:
                    if re.match(r'^\d{4}$', t) and not is_fake(t):
                        row_result = t
                    elif len(t) > 3 and not re.match(r'^[\d/\-:. ]+$', t):
                        row_name = t
                if row_name and row_result:
                    key = match_key(row_name)
                    if key and key not in result:
                        result[key] = _make_entry(row_result, key)
                        print(f"    [{key.upper():6s}] {row_result}  ← \"{row_name}\" (tabel)")

    # ── Strategi C: brute-force proximity ───────────
    if len(result) < 5:
        print(f"  Strategi C: brute-force seluruh halaman")
        all_tags = soup.find_all(['span','div','td','p','li'])
        tag_texts = [(tag.get_text(strip=True), tag) for tag in all_tags]

        # Pasangkan setiap angka 4D dengan nama terdekat (dalam 5 tag sebelumnya)
        name_window = []
        for text, tag in tag_texts:
            if len(text) > 3 and not re.match(r'^[\d/\-:. ]+$', text):
                name_window.append(text)
                if len(name_window) > 5:
                    name_window.pop(0)
            elif re.match(r'^\d{4}$', text) and not is_fake(text):
                for candidate in reversed(name_window):
                    key = match_key(candidate)
                    if key and key not in result:
                        result[key] = _make_entry(text, key)
                        print(f"    [{key.upper():6s}] {text}  ← \"{candidate}\" (brute-force)")
                        break

    print(f"\n  Total parsed: {len(result)} pasaran dari /paito-harian/")
    return result


def _make_entry(result4d, key):
    return {
        'result':     result4d,
        'tgl':        TODAY,
        'fetch_date': list(TODAY_T),
        'status':     'sudah',
        'updated':    NOW.strftime('%H:%M WIB'),
        'name':       PASARAN_NAMES.get(key, key.upper()),
        'source':     'paito-harian',
    }


# ───────────────────────────────────────────────
# FALLBACK: fetch individual (untuk yang missed)
# ───────────────────────────────────────────────
PASARAN_URLS = {
    'hk':   '/data-pengeluaran-togel-hongkong-pools/',
    'hkl':  '/data-pengeluaran-togel-hklotto/',
    'sgp':  '/data-pengeluaran-togel-singapore/',
    'sdy':  '/data-pengeluaran-togel-sydney-pools/',
    'sdl':  '/data-pengeluaran-togel-sdlotto/',
    'kam':  '/data-pengeluaran-togel-magnum-cambodia/',
    'bull': '/data-pengeluaran-togel-bullseye/',
    'chn':  '/data-pengeluaran-togel-chinapools/',
    'jpn':  '/data-pengeluaran-togel-japan/',
    'twn':  '/data-pengeluaran-togel-taiwan/',
    'pcso': '/data-pengeluaran-togel-pcso/',
    'mac1': '/data-pengeluaran-togel-toto-macau-1/',
    'mac2': '/data-pengeluaran-togel-toto-macau-2/',
    'mac3': '/data-pengeluaran-togel-toto-macau-3/',
    'mac4': '/data-pengeluaran-togel-toto-macau-4/',
    'mac5': '/data-pengeluaran-togel-toto-macau-5/',
    'mac6': '/data-pengeluaran-togel-toto-macau-6/',
    'mrq3': '/data-pengeluaran-togel-morocco-quatro-03-00-wib/',
    'mrq18':'/data-pengeluaran-togel-morocco-quatro-18-00-wib/',
    'mrq21':'/data-pengeluaran-togel-morocco-quatro-21-00-wib/',
    'mrq23':'/data-pengeluaran-togel-morocco-quatro-23-59-wib/',
    'ger':  '/data-pengeluaran-togel-germany-plus5/',
    'or4':  '/data-pengeluaran-togel-oregon-04-00-wib/',
    'or7':  '/data-pengeluaran-togel-oregon-07-00-wib/',
    'or10': '/data-pengeluaran-togel-oregon-10-00-wib/',
    'or13': '/data-pengeluaran-togel-oregon-13-00-wib/',
    'ncd':  '/data-pengeluaran-togel-north-carolina-day/',
    'nce':  '/data-pengeluaran-togel-north-carolina-evening/',
    'geom': '/data-pengeluaran-togel-georgia-midday/',
    'geoe': '/data-pengeluaran-togel-georgia-evening/',
    'geon': '/data-pengeluaran-togel-georgia-night/',
    'txd':  '/data-pengeluaran-togel-texas-day/',
    'txmr': '/data-pengeluaran-togel-texas-morning/',
    'txe':  '/data-pengeluaran-togel-texas-evening/',
    'txn':  '/data-pengeluaran-togel-texas-night/',
    'nyd':  '/data-pengeluaran-togel-new-york-midday/',
    'nye':  '/data-pengeluaran-togel-new-york-evening/',
    'njm':  '/data-pengeluaran-togel-new-jersey-midday/',
    'nje':  '/data-pengeluaran-togel-new-jersey-evening/',
    'flm':  '/data-pengeluaran-togel-florida-midday/',
    'fle':  '/data-pengeluaran-togel-florida-evening/',
    'ilm':  '/data-pengeluaran-togel-illinois-midday/',
    'ile':  '/data-pengeluaran-togel-illinois-evening/',
    'indm': '/data-pengeluaran-togel-indiana-midday/',
    'inde': '/data-pengeluaran-togel-indiana-evening/',
    'kym':  '/data-pengeluaran-togel-kentucky-midday/',
    'kye':  '/data-pengeluaran-togel-kentucky-evening/',
    'mdm':  '/data-pengeluaran-togel-maryland-midday/',
    'mde':  '/data-pengeluaran-togel-maryland-evening/',
    'mim':  '/data-pengeluaran-togel-michigan-midday/',
    'mie':  '/data-pengeluaran-togel-michigan-evening/',
    'mom':  '/data-pengeluaran-togel-missouri-midday/',
    'moe':  '/data-pengeluaran-togel-missouri-evening/',
    'wdm':  '/data-pengeluaran-togel-washington-dc-midday/',
    'wde':  '/data-pengeluaran-togel-washington-dc-evening/',
    'ctd':  '/data-pengeluaran-togel-connecticut-day/',
    'ctn':  '/data-pengeluaran-togel-connecticut-night/',
    'vad':  '/data-pengeluaran-togel-virginia-day/',
    'van':  '/data-pengeluaran-togel-virginia-night/',
    'tnm':  '/data-pengeluaran-togel-tennesse-midday/',
    'tne':  '/data-pengeluaran-togel-tennesse-evening/',
    'tnmr': '/data-pengeluaran-togel-tennesse-morning/',
    'cal':  '/data-pengeluaran-togel-california/',
    'wie':  '/data-pengeluaran-togel-wisconsin-evening/',
    'wim':  '/data-pengeluaran-togel-wisconsin-midday/',
}

def fetch_individual(key):
    """Fallback fetch per-pasaran (sama seperti versi lama)."""
    path = PASARAN_URLS.get(key)
    if not path:
        return None

    for url, hdrs in [
        (BASE + path, dict(HEADERS)),
        (f'https://{DIRECT_IP}{path}', {**HEADERS, 'Host': 'angkanet18.com'}),
    ]:
        try:
            time.sleep(0.4)
            r = requests.get(url, headers=hdrs, timeout=15, verify=False)
            if r.status_code == 525:
                continue
            r.raise_for_status()

            # Cari 4D valid
            soup = BeautifulSoup(r.text, 'html.parser')

            # Priority: paito-row-item
            items = soup.find_all(class_='paito-row-item')
            for item in items:
                t = item.get_text(strip=True)
                if re.match(r'^\d{4}$', t) and not is_fake(t):
                    print(f"    [{key.upper():6s}] {t}  (individual fallback)")
                    return _make_entry(t, key)

            # Fallback: semua span/td
            for tag in soup.find_all(['span', 'td']):
                t = tag.get_text(strip=True)
                if re.match(r'^\d{4}$', t) and not is_fake(t):
                    print(f"    [{key.upper():6s}] {t}  (individual fallback span/td)")
                    return _make_entry(t, key)

        except Exception as e:
            print(f"    [{key.upper():6s}] ERR individual: {e}")
            continue

    return None


# ───────────────────────────────────────────────
# MAIN
# ───────────────────────────────────────────────
def main():
    print(f"\n{'='*60}")
    print(f"fetch_all.py (paito-harian mode)")
    print(f"{NOW.strftime('%A, %d %B %Y %H:%M WIB')}")
    print(f"Total pasaran: {len(ALL_KEYS)}")
    print(f"{'='*60}\n")

    # Load data lama
    try:
        with open('result.json', 'r', encoding='utf-8') as f:
            saved = json.load(f)
        print(f"Data lama: {len([k for k in saved if not k.startswith('_')])} pasaran\n")
    except Exception:
        saved = {}
        print("Tidak ada data lama.\n")

    result_data = {k: v for k, v in saved.items()
                   if k in ALL_KEYS or k.startswith('_')}

    # ── STEP 1: Fetch bulk dari /paito-harian/ ──
    print("STEP 1 — Bulk fetch /paito-harian/ ...\n")
    bulk = fetch_paito_harian()

    # Merge bulk ke result_data
    for key, entry in bulk.items():
        old = result_data.get(key, {})
        old_res = old.get('result', '')
        # Jangan overwrite data hari ini yang valid dengan data baru jika sama kualitasnya
        if old.get('fetch_date') == list(TODAY_T) and not is_fake(old_res):
            # Sudah ada data hari ini — update saja jika result berubah
            if old_res != entry['result']:
                print(f"  [{key.upper():6s}] UPDATE {old_res} → {entry['result']}")
                result_data[key] = entry
            else:
                result_data[key] = entry  # refresh timestamp
        else:
            result_data[key] = entry

    # ── STEP 2: Fallback individual untuk yang masih kosong ──
    missing = [k for k in ALL_KEYS
               if k not in bulk and (
                   k not in result_data
                   or is_fake(result_data[k].get('result', ''))
                   or result_data[k].get('fetch_date') != list(TODAY_T)
               )]

    if missing:
        print(f"\nSTEP 2 — Individual fallback untuk {len(missing)} pasaran: {missing}\n")
        for key in missing:
            entry = fetch_individual(key)
            if entry:
                result_data[key] = entry
            elif key not in result_data:
                result_data[key] = {
                    'result': '----',
                    'tgl': TODAY,
                    'status': 'belum',
                    'updated': NOW.strftime('%H:%M WIB'),
                    'name': PASARAN_NAMES.get(key, key.upper()),
                }
            else:
                old_res = result_data[key].get('result', '')
                if not is_fake(old_res):
                    print(f"  [{key.upper():6s}] Pakai data lama: {old_res}")
                else:
                    result_data[key]['result'] = '----'
                    result_data[key]['status'] = 'belum'
    else:
        print("\nSTEP 2 — Semua pasaran sudah dapat dari paito-harian, skip fallback ✓")

    # ── META ──
    ok = [k for k in ALL_KEYS
          if re.match(r'^\d{4}$', result_data.get(k, {}).get('result', ''))]

    result_data['_meta'] = {
        'updated': NOW.strftime('%Y-%m-%d %H:%M WIB'),
        'date':    TODAY,
        'total':   len(ALL_KEYS),
        'ok':      len(ok),
        'source':  'paito-harian',
    }

    # ── SAVE ──
    with open('result.json', 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)

    print(f"\n{'='*60}")
    print(f"result.json tersimpan")
    print(f"  ✓ Valid  : {len(ok)}")
    print(f"  ✗ Belum  : {len(ALL_KEYS) - len(ok)}")
    print(f"  Source   : paito-harian (1 request) + {len(missing)} individual fallback")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
