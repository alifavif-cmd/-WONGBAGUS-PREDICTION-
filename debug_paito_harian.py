"""
Debug script khusus untuk analisis struktur paito-harian
Upload dan jalankan ini di GitHub Actions untuk melihat struktur aslinya
"""
import requests
import urllib3
urllib3.disable_warnings()
from bs4 import BeautifulSoup

BASE = 'https://angkanet18.com'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

url = f'{BASE}/paito-harian/'
r = requests.get(url, headers=HEADERS, timeout=20, verify=False)
print(f"Status: {r.status_code}  len: {len(r.text)}")

soup = BeautifulSoup(r.text, 'html.parser')

# 1. Semua class unik pada halaman
print("\n=== SEMUA CLASS UNIK (top 40 paling sering) ===")
from collections import Counter
all_classes = []
for el in soup.find_all(True):
    for c in (el.get('class') or []):
        all_classes.append(c)
cc = Counter(all_classes)
for cls, cnt in cc.most_common(40):
    print(f"  .{cls}: {cnt}x")

# 2. Struktur tabel jika ada
print("\n=== TABEL (5 pertama) ===")
for i, tbl in enumerate(soup.find_all('table')[:5]):
    print(f"  Table {i}: class={tbl.get('class')}, rows={len(tbl.find_all('tr'))}")
    # Header row
    for j, tr in enumerate(tbl.find_all('tr')[:3]):
        cells = [td.get_text(strip=True)[:30] for td in tr.find_all(['th','td'])]
        print(f"    row {j}: {cells}")

# 3. Elemen dengan class 'paito' atau 'result'
print("\n=== ELEMEN PAITO/RESULT (10 pertama) ===")
import re
for el in soup.find_all(True, class_=re.compile(r'paito|result|angka|number', re.I))[:10]:
    txt = el.get_text(' ', strip=True)[:80]
    print(f"  <{el.name} class={el.get('class')}> {txt!r}")

# 4. Semua heading h1-h4
print("\n=== HEADINGS h1-h4 (20 pertama) ===")
for h in soup.find_all(['h1','h2','h3','h4'])[:20]:
    print(f"  <{h.name} class={h.get('class')}> {h.get_text(strip=True)[:60]!r}")

# 5. Elemen yang teksnya adalah 4 digit
print("\n=== ELEMEN TEKS 4-DIGIT (20 pertama) ===")
import re as _re
count4 = 0
for el in soup.find_all(True):
    t = el.get_text(strip=True)
    if _re.match(r'^\d{4}$', t):
        parent_cls = el.parent.get('class') if el.parent else None
        grandp_cls = el.parent.parent.get('class') if (el.parent and el.parent.parent) else None
        print(f"  <{el.name} class={el.get('class')}> '{t}' | parent={parent_cls} | gp={grandp_cls}")
        count4 += 1
        if count4 >= 20:
            break

# 6. Cari div/section dengan banyak angka (kandidat blok data)
print("\n=== DIV/SECTION DENGAN BANYAK ANGKA 4-DIGIT ===")
for el in soup.find_all(['div','section','article']):
    txt = el.get_text(' ')
    nums = _re.findall(r'\b\d{4}\b', txt)
    if len(nums) >= 5:
        cls = el.get('class')
        id_ = el.get('id')
        print(f"  <{el.name} class={cls} id={id_}> {len(nums)} angka, sample: {nums[:5]}")
        # Cetak 200 char pertama dari teks
        print(f"    TEXT: {txt[:200]!r}")
        print()

