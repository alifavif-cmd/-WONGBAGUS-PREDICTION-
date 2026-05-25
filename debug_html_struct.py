"""
debug_html_struct.py v2 — Print isi actual column1, tampil, paito-line
"""
import requests, re, urllib3
from bs4 import BeautifulSoup
urllib3.disable_warnings()

BASE = 'https://angkanet18.com'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8',
}

r = requests.get(f'{BASE}/data-pengeluaran-togel-hongkong-pools/',
                 headers=HEADERS, timeout=20, verify=False)
print(f"Status: {r.status_code}  len: {len(r.text):,}")
soup = BeautifulSoup(r.text, 'html.parser')

# Print 5 contoh isi .column1
print("\n=== ISI .column1 (5 pertama) ===")
for el in soup.find_all(class_='column1')[:5]:
    print(f"  TEXT: '{el.get_text(strip=True)}'")
    print(f"  HTML: {str(el)[:200]}")
    print()

# Print 5 contoh isi .tampil
print("\n=== ISI .tampil (5 pertama) ===")
for el in soup.find_all(class_='tampil')[:5]:
    print(f"  TEXT: '{el.get_text(strip=True)}'")
    print(f"  HTML: {str(el)[:200]}")
    print()

# Print 3 contoh isi .paito-line (outerHTML singkat)
print("\n=== ISI .paito-line (3 pertama, max 300 char) ===")
for el in soup.find_all(class_='paito-line')[:3]:
    print(f"  TEXT items: {[c.get_text(strip=True) for c in el.find_all(True)][:10]}")
    print(f"  HTML: {str(el)[:300]}")
    print()

# Print 3 contoh isi .paito-row-item beserta parent-nya
print("\n=== .paito-row-item (3 pertama) + parent ===")
for el in soup.find_all(class_='paito-row-item')[:3]:
    print(f"  ITEM TEXT: '{el.get_text(strip=True)}'")
    parent = el.parent
    print(f"  PARENT class: {parent.get('class')}")
    print(f"  PARENT HTML: {str(parent)[:300]}")
    print()
