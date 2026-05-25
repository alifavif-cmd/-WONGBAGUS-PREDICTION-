"""
debug_find_kode.py — Cari parameter 'kode' untuk API bot-trek
dari dalam HTML halaman pasaran angkanet18.com
"""
import requests
import re
import json
import urllib3
urllib3.disable_warnings()

DIRECT_IP = '159.65.133.131'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/124.0 Safari/537.36',
    'Accept': 'text/html,*/*;q=0.9',
    'Host': 'angkanet18.com',
}

TARGETS = [
    ('hk',  '/data-pengeluaran-togel-hongkong-pools/'),
    ('sgp', '/data-pengeluaran-togel-singapore/'),
    ('sdy', '/data-pengeluaran-togel-sydney-pools/'),
]

def find_kode(html, label):
    print(f"\n{'='*60}")
    print(f"PASARAN: {label.upper()}")
    print('='*60)

    # 1. Cari semua script tag, search keyword wla/bot-trek/kode
    scripts = re.findall(r'<script[^>]*>(.*?)</script>', html, re.S)
    print(f"\n--- Script tags: {len(scripts)} ---")
    for i, sc in enumerate(scripts):
        sc_short = sc[:2000]
        if any(kw in sc_short.lower() for kw in ['wla', 'bot-trek', 'kode', 'pasaran', 'trek']):
            print(f"\n[Script #{i}] (relevant):")
            print(sc_short[:1500])

    # 2. Cari data-* attribute yang mengandung kode
    print(f"\n--- data-* attributes mengandung angka/kode ---")
    for m in re.finditer(r'data-[\w-]+=(["\'])([^"\']{2,40})\1', html):
        val = m.group(2)
        if re.match(r'^[\w\-]+$', val) and not re.match(r'^https?:', val):
            ctx = html[max(0,m.start()-50):m.start()+80]
            print(f"  {m.group(0)[:60]}  →  ctx: {ctx[:80]!r}")

    # 3. Cari JSON object yang ada field 'kode' atau 'pasaran_id'
    print(f"\n--- JSON dengan field kode/pasaran ---")
    for m in re.finditer(r'\{[^{}]{0,500}\b(?:kode|pasaran_id|market_id)\b[^{}]{0,500}\}', html, re.S):
        print(f"  {m.group()[:200]}")

    # 4. Cari var/const/let yang assign string pendek (kandidat kode)
    print(f"\n--- JS variable assignment pendek ---")
    for m in re.finditer(r'(?:var|let|const)\s+(\w+)\s*=\s*["\']([a-z0-9_\-]{2,30})["\']', html, re.I):
        print(f"  {m.group()} ")

    # 5. Test langsung API bot-trek dengan beberapa kemungkinan kode
    print(f"\n--- Test API bot-trek ---")
    # Ekstrak semua string pendek unik dari script tags yang mungkin kode
    candidates = set()
    for sc in scripts:
        # Cari string 3-30 char setelah keyword 'kode'
        for m in re.finditer(r'kode["\']?\s*[:=]\s*["\']([^"\']{2,30})["\']', sc, re.I):
            candidates.add(m.group(1))
        # Cari dalam JSON-like struktur
        for m in re.finditer(r'"kode"\s*:\s*"([^"]{2,30})"', sc):
            candidates.add(m.group(1))

    if candidates:
        print(f"  Kandidat kode dari HTML: {candidates}")
        for kode in candidates:
            try:
                r = requests.post(
                    f'https://{DIRECT_IP}/wp-json/wla/v1/bot-trek',
                    json={'kode': kode},
                    headers={**HEADERS, 'Content-Type': 'application/json'},
                    timeout=8, verify=False
                )
                print(f"  POST kode={kode!r} → {r.status_code} {r.text[:200]}")
            except Exception as e:
                print(f"  POST kode={kode!r} → ERR {e}")
    else:
        print("  Tidak ada kandidat kode ditemukan di HTML")

    # 6. Langsung test dengan slug URL pasaran
    slug = label  # coba slug dari URL
    url_slug = re.search(r'/data-pengeluaran-togel-([^/]+)/', TARGETS[0][1])
    slug2 = url_slug.group(1) if url_slug else label
    for kode_try in [label, slug2]:
        try:
            r = requests.post(
                f'https://{DIRECT_IP}/wp-json/wla/v1/bot-trek',
                json={'kode': kode_try},
                headers={**HEADERS, 'Content-Type': 'application/json'},
                timeout=8, verify=False
            )
            print(f"  POST kode={kode_try!r} → {r.status_code} {r.text[:200]}")
        except Exception as e:
            print(f"  POST kode={kode_try!r} → ERR {e}")


# ─── MAIN ───
for label, path in TARGETS:
    url = f'http://{DIRECT_IP}{path}'
    print(f"\nFetching {label.upper()} ← {url}")
    try:
        r = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        print(f"Status: {r.status_code}  Size: {len(r.text):,} bytes")
        if r.status_code == 200 and len(r.text) > 5000:
            find_kode(r.text, label)
        else:
            print("  SKIP: response error/kecil")
    except Exception as e:
        print(f"  ERROR: {e}")

print("\n\nSelesai!")
