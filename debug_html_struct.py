"""
debug_html_struct.py — Cek struktur HTML halaman pasaran individual
Jalankan sekali untuk lihat apakah data ada di static HTML atau JS-rendered
"""
import requests, re, urllib3
from bs4 import BeautifulSoup
urllib3.disable_warnings()

BASE = 'https://angkanet18.com'
DIRECT_IP = '159.65.133.131'
PATH = '/data-pengeluaran-togel-hongkong-pools/'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8',
}

def fetch(url, hdrs):
    try:
        r = requests.get(url, headers=hdrs, timeout=20, verify=False, allow_redirects=True)
        print(f"  Status: {r.status_code}  len: {len(r.text):,} chars")
        return r.text if len(r.text) > 500 else None
    except Exception as e:
        print(f"  ERR: {e}")
        return None

print("="*60)
print(f"Target: {BASE+PATH}")
print("="*60)

html = fetch(BASE + PATH, HEADERS)
if not html:
    print("Coba via IP langsung...")
    html = fetch(f'https://{DIRECT_IP}{PATH}', {**HEADERS, 'Host': 'angkanet18.com'})

if not html:
    print("GAGAL fetch HTML")
    exit()

soup = BeautifulSoup(html, 'html.parser')

# 1. Cek paito-row-item
items = soup.find_all(class_='paito-row-item')
print(f"\n[1] paito-row-item count: {len(items)}")
if items:
    for i in items[:5]:
        print(f"    '{i.get_text(strip=True)}'")

# 2. Cek semua class yang ada (top 20 paling banyak)
from collections import Counter
all_classes = []
for tag in soup.find_all(True):
    for c in (tag.get('class') or []):
        all_classes.append(c)
top_classes = Counter(all_classes).most_common(20)
print(f"\n[2] Top 20 CSS classes di halaman:")
for cls, n in top_classes:
    print(f"    {n:4d}x  .{cls}")

# 3. Cari angka 4 digit di halaman
digits4 = re.findall(r'\b(\d{4})\b', html)
freq4 = Counter(digits4).most_common(15)
print(f"\n[3] Angka 4 digit paling sering muncul:")
for d, n in freq4:
    print(f"    {n:3d}x  {d}")

# 4. Cari pola tanggal
dates = re.findall(r'\d{2}[/-]\d{2}[/-]\d{4}|\d{4}[/-]\d{2}[/-]\d{2}', html)
print(f"\n[4] Pola tanggal ditemukan: {len(dates)}")
for d in dates[:10]:
    print(f"    {d}")

# 5. Cek apakah ada tanda JS-rendering
js_markers = ['var wlaData', 'window.__', 'json_data', 'api_data',
               'fetch(', 'axios', 'XMLHttpRequest', 'wp-json']
print(f"\n[5] JS marker check:")
for m in js_markers:
    found = m in html
    print(f"    {'✓' if found else '✗'}  {m}")

# 6. Dump 500 char dari area yang mengandung angka 4 digit pertama
match = re.search(r'\b\d{4}\b', html)
if match:
    start = max(0, match.start() - 200)
    end   = min(len(html), match.end() + 300)
    print(f"\n[6] Context sekitar angka 4 digit pertama:")
    snippet = html[start:end].replace('\n', ' ').replace('  ', ' ')
    print(f"    {snippet[:500]}")

print("\n" + "="*60)
print("Selesai.")
