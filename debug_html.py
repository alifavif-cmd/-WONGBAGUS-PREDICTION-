"""
debug_html.py — Dump struktur HTML dari angkanet ke log GitHub Actions
Jalankan sekali saja, lalu hapus dari repo.
"""
import requests
import re
from bs4 import BeautifulSoup
import urllib3
urllib3.disable_warnings()

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36',
    'Accept': 'text/html,*/*;q=0.9',
    'Accept-Language': 'id-ID,id;q=0.9',
}

# Fetch beberapa pasaran — pilih yang paling sering berhasil
TARGETS = [
    ('mrq23', 'http://159.65.133.131/data-pengeluaran-togel-morocco-quatro-23-59-wib/'),
    ('mrq21', 'http://159.65.133.131/data-pengeluaran-togel-morocco-quatro-21-00-wib/'),
    ('hk',    'http://159.65.133.131/data-pengeluaran-togel-hongkong-pools/'),
    ('sgp',   'http://159.65.133.131/data-pengeluaran-togel-singapore/'),
]

def analyze(key, html):
    print(f"\n{'='*70}")
    print(f"PASARAN: {key.upper()}  |  HTML size: {len(html)} bytes")
    print('='*70)

    soup = BeautifulSoup(html, 'html.parser')

    # 1. Semua <td> yang isinya 1-6 digit
    print("\n--- <td> berisi angka ---")
    tds = soup.find_all('td')
    for td in tds[:60]:
        t = td.get_text(strip=True)
        if re.match(r'^\d{1,6}$', t):
            cls = td.get('class', [])
            print(f"  <td class={cls}> = {t!r}")

    # 2. Semua elemen dengan data-* attribute mengandung angka
    print("\n--- elemen dengan data-* angka ---")
    for el in soup.find_all(True):
        for attr, val in el.attrs.items():
            if attr.startswith('data-') and isinstance(val, str) and re.match(r'^\d{3,6}$', val):
                print(f"  <{el.name} {attr}={val!r} class={el.get('class',[])}> text={el.get_text(strip=True)[:30]!r}")

    # 3. Elemen dengan class mengandung kata kunci result
    print("\n--- class mengandung result/paito/angka/4d ---")
    for el in soup.find_all(class_=re.compile(r'result|paito|angka|4d|keluaran|prize|number|tbl|table', re.I)):
        t = el.get_text(strip=True)[:80]
        nums = re.findall(r'\b\d{4}\b', t)
        if nums:
            print(f"  <{el.name} class={el.get('class',[])}> nums={nums} text={t!r}")

    # 4. Semua angka 4-digit unik dalam teks (bukan dalam header/footer)
    for tag in soup.find_all(['header','nav','footer','aside','script','style']):
        tag.decompose()
    text = soup.get_text(' ')
    all4 = list(dict.fromkeys(re.findall(r'\b(\d{4})\b', text)))
    print(f"\n--- Semua angka 4-digit unik (setelah hapus header/footer) ---")
    print(f"  {all4[:40]}")

    # 5. Simpan 200 baris pertama HTML ke file untuk referensi
    lines = html.split('\n')
    snippet = '\n'.join(lines[:200])
    fname = f'debug_{key}.txt'
    with open(fname, 'w', encoding='utf-8') as f:
        f.write(f"URL: http://159.65.133.131/{key}\n")
        f.write(f"Size: {len(html)} bytes\n\n")
        f.write("=== FIRST 200 LINES ===\n")
        f.write(snippet)
        f.write("\n\n=== ALL 4-DIGIT TD ===\n")
        for td in soup.find_all('td'):
            t = td.get_text(strip=True)
            if re.match(r'^\d{4}$', t):
                f.write(f"<td class={td.get('class',[])}>{t}</td>\n")
    print(f"\n  Saved: {fname}")

for key, url in TARGETS:
    print(f"\nFetching {key.upper()} <- {url}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        print(f"Status: {r.status_code}  Size: {len(r.text)} bytes")
        if r.status_code == 200 and len(r.text) > 1000:
            analyze(key, r.text)
        else:
            print("  SKIP: response terlalu kecil atau error")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\n\nSelesai! Cek file debug_*.txt yang ter-commit di repo.")
