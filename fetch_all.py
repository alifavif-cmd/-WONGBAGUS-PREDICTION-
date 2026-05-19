"""
fetch_all.py — Fetch 65 pasaran togel dari angkanet.com (159.65.133.131)
Diperbarui: Menggunakan penargetan tabel akurat agar data TIDAK NGAWUR,
dan dilengkapi Multi-threading agar proses fetch selesai dalam hitungan detik.
"""

import requests
import json
import re
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
from concurrent.futures import ThreadPoolExecutor, as_completed

# ===== TIMEZONE =====
WIB = timezone(timedelta(hours=7))
NOW = datetime.now(WIB)
TODAY = NOW.strftime('%d/%m')

BASE = 'https://159.65.133.131'

# ===== DAFTAR 65 PASARAN =====
PASARAN = {
    # === ASIA UTAMA ===
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
    # === TOTO MACAU (6 sesi) ===
    'mac':  ('/data-pengeluaran-togel-toto-macau-1/',   'Macau (alias)'),
    'mac1': ('/data-pengeluaran-togel-toto-macau-1/',   'Toto Macau 13'),
    'mac2': ('/data-pengeluaran-togel-toto-macau-2/',   'Toto Macau 16'),
    'mac3': ('/data-pengeluaran-togel-toto-macau-3/',   'Toto Macau 19'),
    'mac4': ('/data-pengeluaran-togel-toto-macau-4/',   'Toto Macau 22'),
    'mac5': ('/data-pengeluaran-togel-toto-macau-5/',   'Toto Macau 00'),
    'mac6': ('/data-pengeluaran-togel-toto-macau-6/',   'Toto Macau 23'),
    # === MOROCCO QUATRO (4 sesi) ===
    'mrq3':  ('/data-pengeluaran-togel-morocco-quatro-03-00-wib/', 'Morocco 03:00'),
    'mrq18': ('/data-pengeluaran-togel-morocco-quatro-18-00-wib/', 'Morocco 18:00'),
    'mrq21': ('/data-pengeluaran-togel-morocco-quatro-21-00-wib/', 'Morocco 21:00'),
    'mrq23': ('/data-pengeluaran-togel-morocco-quatro-23-59-wib/', 'Morocco 23:59'),
    # === GERMANY ===
    'ger':  ('/data-pengeluaran-togel-germany-plus5/', 'Germany Plus5'),
    # === OREGON (4 sesi) ===
    'or4':  ('/data-pengeluaran-togel-oregon-04-00-wib/', 'Oregon 04:00'),
    'or7':  ('/data-pengeluaran-togel-oregon-07-00-wib/', 'Oregon 07:00'),
    'or10': ('/data-pengeluaran-togel-oregon-10-00-wib/', 'Oregon 10:00'),
    'or13': ('/data-pengeluaran-togel-oregon-13-00-wib/', 'Oregon 13:00'),
    # === NORTH CAROLINA ===
    'ncd':  ('/data-pengeluaran-togel-north-carolina-day/',     'NC Day'),
    'nce':  ('/data-pengeluaran-togel-north-carolina-evening/', 'NC Evening'),
    # === GEORGIA ===
    'geom': ('/data-pengeluaran-togel-georgia-midday/',  'Georgia Midday'),
    'geoe': ('/data-pengeluaran-togel-georgia-evening/', 'Georgia Evening'),
    'geon': ('/data-pengeluaran-togel-georgia-night/',   'Georgia Night'),
    # === TEXAS ===
    'txd':  ('/data-pengeluaran-togel-texas-day/',     'Texas Day'),
    'txmr': ('/data-pengeluaran-togel-texas-morning/', 'Texas Morning'),
    'txe':  ('/data-pengeluaran-togel-texas-evening/', 'Texas Evening'),
    'txn':  ('/data-pengeluaran-togel-texas-night/',   'Texas Night'),
    # === NEW YORK ===
    'nyd':  ('/data-pengeluaran-togel-new-york-midday/',  'New York Midday'),
    'nye':  ('/data-pengeluaran-togel-new-york-evening/', 'New York Evening'),
    # === NEW JERSEY ===
    'njm':  ('/data-pengeluaran-togel-new-jersey-midday/',  'NJ Midday'),
    'nje':  ('/data-pengeluaran-togel-new-jersey-evening/', 'NJ Evening'),
    # === FLORIDA ===
    'flm':  ('/data-pengeluaran-togel-florida-midday/',  'Florida Midday'),
    'fle':  ('/data-pengeluaran-togel-florida-evening/', 'Florida Evening'),
    # === ILLINOIS ===
    'ilm':  ('/data-pengeluaran-togel-illinois-midday/',  'Illinois Midday'),
    'ile':  ('/data-pengeluaran-togel-illinois-evening/', 'Illinois Evening'),
    # === INDIANA ===
    'indm': ('/data-pengeluaran-togel-indiana-midday/',  'Indiana Midday'),
    'inde': ('/data-pengeluaran-togel-indiana-evening/', 'Indiana Evening'),
    # === KENTUCKY ===
    'kym':  ('/data-pengeluaran-togel-kentucky-midday/',  'Kentucky Midday'),
    'kye':  ('/data-pengeluaran-togel-kentucky-evening/', 'Kentucky Evening'),
    # === MARYLAND ===
    'mdm':  ('/data-pengeluaran-togel-maryland-midday/',  'Maryland Midday'),
    'mde':  ('/data-pengeluaran-togel-maryland-evening/', 'Maryland Evening'),
    # === MICHIGAN ===
    'mim':  ('/data-pengeluaran-togel-michigan-midday/',  'Michigan Midday'),
    'mie':  ('/data-pengeluaran-togel-michigan-evening/', 'Michigan Evening'),
    # === MISSOURI ===
    'mom':  ('/data-pengeluaran-togel-missouri-midday/',  'Missouri Midday'),
    'moe':  ('/data-pengeluaran-togel-missouri-evening/', 'Missouri Evening'),
    # === WASHINGTON DC ===
    'wdm':  ('/data-pengeluaran-togel-washington-dc-midday/',  'WDC Midday'),
    'wde':  ('/data-pengeluaran-togel-washington-dc-evening/', 'WDC Evening'),
    # === CONNECTICUT ===
    'ctd':  ('/data-pengeluaran-togel-connecticut-day/',   'Connecticut Day'),
    'ctn':  ('/data-pengeluaran-togel-connecticut-night/', 'Connecticut Night'),
    # === VIRGINIA ===
    'vad':  ('/data-pengeluaran-togel-virginia-day/',   'Virginia Day'),
    'van':  ('/data-pengeluaran-togel-virginia-night/', 'Virginia Night'),
    # === TENNESSEE ===
    'tnm':  ('/data-pengeluaran-togel-tennesse-midday/',  'Tennessee Midday'),
    'tne':  ('/data-pengeluaran-togel-tennesse-evening/', 'Tennessee Evening'),
    'tnmr': ('/data-pengeluaran-togel-tennesse-morning/', 'Tennessee Morning'),
    # === CALIFORNIA, WISCONSIN ===
    'cal':  ('/data-pengeluaran-togel-california/',        'California'),
    'wie':  ('/data-pengeluaran-togel-wisconsin-evening/', 'Wisconsin Evening'),
}

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8',
    'Connection': 'keep-alive'
}

# Blokir angka urut/kembar palsu bawaan template web
FAKE_PATTERNS = [
    r'^1234$', r'^2345$', r'^3456$', r'^4567$', r'^5678$',
    r'^6789$', r'^7890$', r'^8901$', r'^9012$', r'^0123$',
    r'^(\d)\1{3}$', 
]

def is_year(result):
    try:
        n = int(result)
        return 1800 <= n <= 2099
    except ValueError:
        return False

def is_fake(result):
    if not result or not re.match(r'^\d{4}$', result):
        return True
    if is_year(result):
        return True
    return any(re.match(p, result) for p in FAKE_PATTERNS)

# ===== EKSTRAK RESULT (AKURASI TINGGI) =====
def extract_result(html):
    if not html or len(html) < 200:
        return None

    soup = BeautifulSoup(html, 'html.parser')
    
    # STRATEGI 1: Cari langsung di dalam sel tabel (td) paito (Paling Valid)
    tables = soup.find_all('table')
    for table in tables:
        rows = table.find_all('tr')
        if rows:
            # Iterasi dari baris paling bawah (atau atas) untuk mencari nomor paito murni
            for row in reversed(rows):
                cells = row.find_all('td')
                for cell in cells:
                    val = cell.get_text(strip=True)
                    val = re.sub(r'\D', '', val) # Buang spasi/karakter non-angka
                    if re.match(r'^\d{4}$', val) and not is_fake(val):
                        return val

    # STRATEGI 2: Fallback jika tabel dimodifikasi, cari elemen paito berdasarkan class khusus
    elements = soup.find_all(['td', 'span', 'strong', 'div'], class_=re.compile(r'(paito|result|angka|output|current)', re.I))
    valid_elements = []
    for el in elements:
        val = el.get_text(strip=True)
        val = re.sub(r'\D', '', val)
        if re.match(r'^\d{4}$', val) and not is_fake(val):
            valid_elements.append(val)
    if valid_elements:
        return valid_elements[-1]

    # STRATEGI 3: Standar teks dengan filter super ketat
    main_content = soup.find('main') or soup.find('div', id='content') or soup
    text = main_content.get_text(' ')
    text = re.sub(r'tersedia\s+\d+\s+result[^\n]*', '', text, flags=re.IGNORECASE)
    text = re.sub(r'memuat\s+data\.+', '', text, flags=re.IGNORECASE)
    text = re.sub(r'sejak\s+\d{4}(-\d{2}-\d{2})?', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(19|20)\d{2}\b', '', text) 

    all_valid = [x for x in re.findall(r'\b(\d{4})\b', text) if not is_fake(x)]
    if all_valid:
        return all_valid[-1]

    return None

# ===== FETCH SATU PASARAN =====
def fetch_pasaran(key, path, name):
    url = BASE + path
    try:
        # verify=False digunakan karena akses ke IP langsung sering merusak jabat tangan SSL
        resp = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        resp.raise_for_status()
        result = extract_result(resp.text)
        if result:
            return key, {'result': result, 'tgl': TODAY, 'status': 'sudah',
                         'updated': datetime.now(WIB).strftime('%H:%M WIB'), 'name': name}
    except Exception as e:
        err_msg = str(e).split(']')[ -1 ] if ']' in str(e) else str(e)[:40]
        print(f"  [{key.upper():6s}] ERR: {err_msg}")
        
    return key, {'result': '----', 'tgl': TODAY, 'status': 'belum',
                 'updated': datetime.now(WIB).strftime('%H:%M WIB'), 'name': name}

# ===== MAIN PROGRAM =====
def main():
    print(f"\n{'='*60}")
    print(f"fetch_all.py — {NOW.strftime('%A, %d %B %Y %H:%M WIB')}")
    print(f"Total pasaran: {len(PASARAN)}")
    print(f"{'='*60}\n")

    # Nonaktifkan warning log SSL dari requests
    requests.packages.urllib3.disable_warnings(requests.packages.urllib3.exceptions.InsecureRequestWarning)

    try:
        with open('result.json', 'r', encoding='utf-8') as f:
            saved = json.load(f)
        print(f"Data lama termuat: {len([k for k in saved if not k.startswith('_')])} pasaran\n")
    except Exception:
        saved = {}
        print("Tidak ada data lama (membuat file baru).\n")

    fetched_results = {}
    
    # Jalankan download secara simultan (Multi-threading) agar sangat cepat
    print("Memulai proses ambil data pasaran secara paralel...")
    with ThreadPoolExecutor(max_workers=15) as executor:
        futures = {executor.submit(fetch_pasaran, key, path, name): key for key, (path, name) in PASARAN.items()}
        for future in as_completed(futures):
            key, entry = future.result()
            fetched_results[key] = entry
            if entry['result'] != '----':
                print(f"  [{key.upper():6s}] BERHASIL -> {entry['result']} ({entry['name']})")
            else:
                print(f"  [{key.upper():6s}] BELUM RILIS / LEWAT JAM TAYANG ({entry['name']})")

    # Satukan data lama dengan hasil fetch baru
    result_data = dict(saved)
    for key, entry in fetched_results.items():
        if entry['result'] != '----':
            result_data[key] = entry
        elif key not in result_data:
            result_data[key] = entry
        else:
            old_result = result_data[key].get('result', '')
            if is_fake(old_result):
                print(f"  [{key.upper():6s}] Data lama '{old_result}' terdeteksi cacat. Reset ke ----")
                result_data[key] = entry

    # Tulis Metadata Akhir
    result_data['_meta'] = {
        'updated': datetime.now(WIB).strftime('%Y-%m-%d %H:%M WIB'),
        'date':    TODAY,
        'total':   len(PASARAN),
    }

    with open('result.json', 'w', encoding='utf-8') as f:
        json.dump(result_data, f, indent=2, ensure_ascii=False)

    ok = [k for k, v in result_data.items() if not k.startswith('_') and re.match(r'^\d{4}$', v.get('result', ''))]
    print(f"\n{'='*60}")
    print(f"result.json SUKSES DIPERBARUI | Valid: {len(ok)} | Belum: {len(PASARAN)-len(ok)}")
    print(f"{'='*60}\n")

if __name__ == '__main__':
    main()
