"""
debug_fetch.py — Dump HTML mentah dari angkanet untuk diagnosa
Jalankan: python debug_fetch.py
Output: debug_hk.html (bisa dibuka di browser atau dikirim ke Claude)
"""

import requests
import re
from bs4 import BeautifulSoup

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8',
    'Referer': 'http://159.65.133.131/',
}

# Test 2 URL: http dan https
URLS_TO_TEST = [
    ('http_hk',  'http://159.65.133.131/data-pengeluaran-togel-hongkong-pools/'),
    ('https_hk', 'https://159.65.133.131/data-pengeluaran-togel-hongkong-pools/'),
    ('http_sgp', 'http://159.65.133.131/data-pengeluaran-togel-singapore/'),
]

def dump_url(label, url):
    print(f'\n{"="*60}')
    print(f'TEST: {label}')
    print(f'URL:  {url}')
    print('='*60)
    try:
        r = requests.get(url, headers=HEADERS, timeout=20, verify=False)
        html = r.text
        print(f'Status: {r.status_code}  |  Size: {len(html)} bytes')

        # Simpan full HTML ke file
        fname = f'debug_{label}.html'
        with open(fname, 'w', encoding='utf-8') as f:
            f.write(html)
        print(f'Saved: {fname}')

        # Parse
        soup = BeautifulSoup(html, 'html.parser')
        text = soup.get_text(' ')

        # Cari semua 4-digit numbers
        all4 = re.findall(r'\b\d{4}\b', text)
        print(f'All 4-digit numbers in text: {all4[:30]}')

        # Cari <td> dengan 4 digit
        tds = [td.get_text(strip=True) for td in soup.find_all('td') if re.match(r'^\d{4}$', td.get_text(strip=True))]
        print(f'<td> with 4-digit only: {tds[:20]}')

        # Cari semua class yang mengandung "result" atau "angka" atau "4d"
        interesting = soup.find_all(class_=re.compile(r'result|angka|4d|paito|keluaran|prize|number', re.I))
        print(f'Elements with result-like class: {len(interesting)}')
        for el in interesting[:5]:
            print(f'  <{el.name} class="{el.get("class")}"> text="{el.get_text(strip=True)[:60]}"')

        # Cari data-* attributes
        data_els = soup.find_all(lambda t: any(a.startswith('data-') for a in t.attrs))
        print(f'Elements with data-* attrs: {len(data_els)}')
        for el in data_els[:10]:
            data_attrs = {k:v for k,v in el.attrs.items() if k.startswith('data-')}
            txt = el.get_text(strip=True)[:40]
            print(f'  <{el.name}> data={data_attrs} text="{txt}"')

        # Cari "script" yang berisi JSON atau variable dengan angka
        for sc in soup.find_all('script'):
            sc_text = sc.string or ''
            if any(kw in sc_text.lower() for kw in ['result', 'paito', '4d', 'hk', 'keluaran']):
                print(f'  [SCRIPT] {sc_text[:300]}')

        # Cek apakah ada "Tersedia" pattern
        tersedia = re.findall(r'Tersedia[^\n]{0,50}', text)
        print(f'Tersedia patterns: {tersedia[:5]}')

        # Snippet dari text (awal, tengah, akhir)
        clean = re.sub(r'\s+', ' ', text).strip()
        print(f'\nText preview (first 500 chars):\n{clean[:500]}')
        print(f'\nText preview (middle):\n{clean[len(clean)//2:len(clean)//2+500]}')
        print(f'\nText preview (last 500 chars):\n{clean[-500:]}')

    except Exception as e:
        print(f'ERROR: {e}')


if __name__ == '__main__':
    import urllib3
    urllib3.disable_warnings()  # suppress SSL warning

    for label, url in URLS_TO_TEST:
        dump_url(label, url)

    print('\n\nSelesai! Kirim file debug_http_hk.html ke Claude untuk diagnosa.')
