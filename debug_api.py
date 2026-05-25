"""
debug_api.py — Cari API endpoint yang dipakai angkanet untuk load data historis.

Jalankan sekali di GitHub Actions (tambah step sementara), atau lokal.
Output: debug_api.txt berisi temuan URL/JSON/endpoints.
"""

import requests, json, re, time, urllib3
urllib3.disable_warnings()

BASE      = 'https://angkanet18.com'
DIRECT_IP = '159.65.133.131'

HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': 'text/html,application/xhtml+xml,*/*;q=0.8',
    'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8',
}

out = []

def log(s=''):
    print(s)
    out.append(str(s))

# ── 1. Fetch paito-harian, cari data di script tags ──
log('='*60)
log('1. ANALISIS SCRIPT TAGS — paito-harian')
log('='*60)

try:
    r = requests.get(f'{BASE}/paito-harian/', headers=HEADERS, timeout=20, verify=False)
    html = r.text
    log(f'HTTP {r.status_code} — {len(html):,} chars')

    # Cari semua <script> yang punya data
    script_blocks = re.findall(r'<script[^>]*>(.*?)</script>', html, re.DOTALL)
    log(f'Script blocks: {len(script_blocks)}')

    for i, blk in enumerate(script_blocks):
        blk = blk.strip()
        if not blk or len(blk) < 20:
            continue

        # Cari JSON objects
        json_hits = re.findall(r'\{["\']?(?:result|data|pasaran|angka|keluaran)["\']?\s*:', blk[:2000])
        # Cari URL patterns
        url_hits  = re.findall(r'(?:fetch|axios|ajax|url|src)\s*[:(=]\s*["\']([^"\']+)["\']', blk[:2000], re.I)
        # Cari WordPress AJAX
        wp_hits   = re.findall(r'(?:ajaxurl|wp_ajax|action)\s*[=:]\s*["\']([^"\']+)', blk[:2000], re.I)
        # Cari variabel data (window.xxx = {...})
        win_vars  = re.findall(r'window\.(\w+)\s*=\s*(\{.{10,200})', blk[:3000], re.DOTALL)

        if json_hits or url_hits or wp_hits or win_vars:
            log(f'\n  Script #{i} ({len(blk)} chars):')
            if json_hits:  log(f'    JSON keys  : {json_hits[:5]}')
            if url_hits:   log(f'    URLs       : {url_hits[:5]}')
            if wp_hits:    log(f'    WP AJAX    : {wp_hits[:5]}')
            if win_vars:
                for k, v in win_vars[:3]:
                    log(f'    window.{k} = {v[:100].strip()}...')

    # Cari semua URL fetch/axios
    all_urls = re.findall(r'(?:fetch|axios\.get)\(["\']([^"\']{5,})["\']', html)
    if all_urls:
        log(f'\n  fetch/axios URLs di halaman:')
        for u in set(all_urls): log(f'    {u}')

    # Cari pola REST API
    rest_apis = re.findall(r'["\'](/(?:api|wp-json|rest|v\d)[^"\']{5,})["\']', html)
    if rest_apis:
        log(f'\n  REST API patterns:')
        for u in set(rest_apis): log(f'    {u}')

    # Cari pola data inline (window.__xxx)
    inline = re.findall(r'var\s+(\w+)\s*=\s*(\[.*?\]|\{.*?\})', html[:50000], re.DOTALL)
    for k, v in inline[:5]:
        if len(v) > 50:
            log(f'  var {k} = {v[:150].strip()}...')

except Exception as e:
    log(f'ERROR: {e}')

# ── 2. Coba URL API umum ──
log('\n' + '='*60)
log('2. PROBE CANDIDATE API ENDPOINTS')
log('='*60)

candidates = [
    '/wp-json/wp/v2/posts?per_page=5',
    '/wp-json/',
    '/api/result/hk',
    '/api/data/hk',
    '/api/paito/hk',
    '/api/keluaran/hk',
    '/data/hk.json',
    '/result/hk.json',
    '/?action=get_result&pasaran=hk',
    '/?action=get_paito&pasaran=hk',
    '/wp-admin/admin-ajax.php',
]

for path in candidates:
    try:
        time.sleep(0.3)
        r = requests.get(BASE + path, headers=HEADERS, timeout=8, verify=False)
        ct = r.headers.get('content-type','')
        log(f'  {r.status_code} {path:45s}  ct={ct[:40]}  len={len(r.text)}')
        if r.status_code == 200 and ('json' in ct or r.text.strip().startswith('{')):
            log(f'    → JSON! Preview: {r.text[:200]}')
    except Exception as e:
        log(f'  ERR {path}: {e}')

# ── 3. Fetch halaman HK individual, cari API call di dalamnya ──
log('\n' + '='*60)
log('3. ANALISIS HALAMAN INDIVIDUAL HK')
log('='*60)

try:
    r = requests.get(f'{BASE}/data-pengeluaran-togel-hongkong-pools/',
                     headers=HEADERS, timeout=20, verify=False)
    html = r.text
    log(f'HTTP {r.status_code} — {len(html):,} chars')

    # Ambil semua src script external
    ext_scripts = re.findall(r'<script[^>]+src=["\']([^"\']+)["\']', html)
    log(f'\n  External scripts ({len(ext_scripts)}):')
    for s in ext_scripts: log(f'    {s}')

    # Cari URL fetch
    urls = re.findall(r'(?:fetch|url|ajax|src)\s*[:(=]\s*["\']([^"\']{5,})["\']', html, re.I)
    if urls:
        log(f'\n  URL patterns:')
        for u in set(urls): log(f'    {u}')

    # Cari data attributes
    data_attrs = re.findall(r'data-(?:url|api|src|id)\s*=\s*["\']([^"\']+)["\']', html)
    if data_attrs:
        log(f'\n  data-* attributes: {data_attrs[:10]}')

    # Dump 500 char pertama body
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, 'html.parser')
    body = soup.body
    if body:
        log(f'\n  Body pertama 500 char:')
        log(body.get_text()[:500])

except Exception as e:
    log(f'ERROR: {e}')

# ── Simpan output ──
with open('debug_api.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))

print('\n→ Hasil disimpan ke debug_api.txt')
print('→ Upload debug_api.txt ke chat untuk analisis selanjutnya.')
