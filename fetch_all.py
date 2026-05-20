"""
fetch_all.py — Fetch 65 pasaran togel dari angkanet (159.65.133.131)
Fitur:
- Threading (10 worker) → selesai ~30 detik
- Auto-blacklist angka noise (muncul di 5+ pasaran = dari template)
- Scan hanya konten utama, skip header/footer
"""

import requests
import json
import re
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
from collections import Counter
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

# ===== TIMEZONE =====
WIB = timezone(timedelta(hours=7))
NOW = datetime.now(WIB)
TODAY = NOW.strftime('%d/%m')

BASE = 'http://159.65.133.131'
TIMEOUT = 8   # detik per request
WORKERS = 10  # fetch paralel

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
    'mac':  ('/data-pengeluaran-togel-toto-macau-1/',   'Macau (alias)'),
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

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,*/*;q=0.9',
    'Accept-Language': 'id-ID,id;q=0.9',
}

FAKE_PATTERNS = [
    r'^(\d)\1{3}$',         # 0000, 1111, 2222 dst
    r'^1234$', r'^2345$', r'^3456$', r'^4567$',
    r'^5678$', r'^6789$', r'^7890$', r'^8901$',
    r'^9012$', r'^0123$',
]

def is_year(n):
    try: return 1800 <= int(n) <= 2099
    except: return False

def is_fake(n):
    if not n or not re.match(r'^\d{4}$', n): return True
    if is_year(n): return True
    return any(re.match(p, n) for p in FAKE_PATTERNS)


# ===== STEP 1: Fetch raw HTML semua pasaran paralel =====
def fetch_html(key, path):
    url = BASE + path
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT, verify=False)
        if r.status_code == 200 and len(r.text) > 500:
            return key, r.text
    except Exception as e:
        pass
    return key, None


# ===== STEP 2: Extract dari HTML, skip header/footer =====
def extract_result(html, noise_set=set()):
    if not html or len(html) < 200:
        return None

    soup = BeautifulSoup(html, 'html.parser')

    # Hapus elemen template (header, nav, footer, sidebar, script)
    for tag in soup.find_all(['header','nav','footer','aside','script','style','noscript']):
        tag.decompose()
    for cls in ['wla-top','wla-nav','wla-header','wla-footer','wla-sidebar',
                'site-header','site-footer','widget','breadcrumb','menu']:
        for el in soup.find_all(class_=re.compile(cls, re.I)):
            el.decompose()

    # Cari area konten utama
    root = (
        soup.find('main') or
        soup.find('article') or
        soup.find(id=re.compile(r'content|main|primary', re.I)) or
        soup.find(class_=re.compile(r'entry.?content|paito|pengeluaran|post.?content', re.I)) or
        soup
    )

    # Cari <td> TEPAT 4 digit (baris pertama = terbaru di paito)
    for td in root.find_all('td'):
        t = td.get_text(strip=True)
        if re.match(r'^\d{4}$', t) and not is_fake(t) and t not in noise_set:
            return t

    # Scan teks konten utama
    text = root.get_text(' ')
    text = re.sub(r'Tersedia\s+\d+\s+result[^\n]*', '', text, flags=re.I)
    text = re.sub(r'\b202[0-9]\b|\b(1[89]\d{2})\b', '', text)
    text = re.sub(r'sejak\s+\d+', '', text, flags=re.I)

    valid = [x for x in re.findall(r'\b(\d{4})\b', text)
             if not is_fake(x) and x not in noise_set]

    return valid[0] if valid else None


# ===== MAIN =====
def main():
    print(f"\n{'='*60}")
    print(f"fetch_all.py — {NOW.strftime('%d %b %Y %H:%M WIB')}")
    print(f"Pasaran: {len(PASARAN)}  |  Workers: {WORKERS}  |  Timeout: {TIMEOUT}s")
    print(f"{'='*60}\n")

    # Load data lama
    try:
        with open('result.json', 'r', encoding='utf-8') as f:
            saved = json.load(f)
    except Exception:
        saved = {}

    # STEP 1: Fetch semua HTML paralel
    print(">> Fetching HTML paralel...")
    raw_htmls = {}
    with ThreadPoolExecutor(max_workers=WORKERS) as ex:
        futures = {ex.submit(fetch_html, k, p): k for k, (p, _) in PASARAN.items()}
        for fut in as_completed(futures):
            key, html = fut.result()
            raw_htmls[key] = html
            status = f"OK ({len(html)} bytes)" if html else "GAGAL"
            print(f"  [{key.upper():6s}] {status}")

    print(f"\n>> Dapat HTML: {sum(1 for v in raw_htmls.values() if v)} / {len(PASARAN)}")

    # STEP 2: Extract hasil mentah (sebelum noise filter)
    print("\n>> Ekstrak angka (belum filter noise)...")
    raw_results = {}
    for key, html in raw_htmls.items():
        raw_results[key] = extract_result(html, noise_set=set())
    
    # STEP 3: Auto-detect noise — angka yang muncul di 5+ pasaran = dari template
    counts = Counter(v for v in raw_results.values() if v)
    auto_noise = {n for n, c in counts.items() if c >= 5}
    if auto_noise:
        print(f"\n!! AUTO-NOISE DETECTED: {auto_noise}")
        print(f"   (muncul di banyak pasaran = dari template header/footer)\n")

    # STEP 4: Re-extract dengan noise filter
    print(">> Re-ekstrak dengan noise filter...")
    result_data = dict(saved)
    for key, (path, name) in PASARAN.items():
        html = raw_htmls.get(key)
        result = extract_result(html, noise_set=auto_noise) if html else None

        print(f"  [{key.upper():6s}] raw={raw_results.get(key)!r:6}  final={result!r}  ({name})")

        if result and not is_fake(result):
            result_data[key] = {
                'result': result, 'tgl': TODAY,
                'status': 'sudah', 'updated': NOW.strftime('%H:%M WIB'), 'name': name
            }
        elif key not in result_data or is_fake(result_data[key].get('result','')):
            result_data[key] = {
                'result': '----', 'tgl': TODAY,
                'status': 'belum', 'updated': NOW.strftime('%H:%M WIB'), 'name': name
            }
        else:
            print(f"  [{key.upper():6s}] Pakai data lama: {result_data[key]['result']}")

    result_data['_meta'] = {
        'updated': NOW.strftime('%Y-%m-%d %H:%M WIB'),
        'date': TODAY, 'total': len(PASARAN),
        'noise': list(auto_noise),
    }

    with open('result.json', 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)

    ok = [k for k, v in result_data.items()
          if not k.startswith('_') and re.match(r'^\d{4}$', v.get('result',''))]
    print(f"\n{'='*60}")
    print(f"Selesai! Valid: {len(ok)} | Belum: {len(PASARAN)-len(ok)}")
    print(f"Noise terdeteksi: {auto_noise}")
    print(f"{'='*60}\n")


if __name__ == '__main__':
    main()
