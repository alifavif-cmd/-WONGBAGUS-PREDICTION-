"""
debug_api.py v9 — Temuan v8:
  - PASARAN = { ditemukan di baris 29
  - 'hk': ('/data-... → perlu lihat lanjutannya
  - Semua slug URL masih invalid → coba numeric ID
"""
import requests, json, re, time, urllib3, os
urllib3.disable_warnings()

BASE    = 'https://angkanet18.com'
HEADERS = {
    'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept'     : 'application/json, */*',
    'Referer'    : 'https://angkanet18.com/',
}
URL_TREK  = f'{BASE}/wp-json/wla/v1/bot-trek'
URL_BATCH = f'{BASE}/wp-json/wla/v1/bot-trek-batch'

out = []
def log(s=''):
    print(s)
    out.append(str(s))

# ══════════════════════════════════════════════════════
log('='*60)
log('A. Dump PASARAN dict (baris 29-200 fetch_all.py)')
log('='*60)

fa_source = ''
for sp in ['fetch_all.py', '/github/workspace/fetch_all.py']:
    if os.path.exists(sp):
        with open(sp, encoding='utf-8') as f:
            fa_source = f.read()
        break

if fa_source:
    lines = fa_source.splitlines()
    # Dump baris 29-200 (index 28-199)
    log('--- Lines 29-200 ---')
    for i in range(28, min(200, len(lines))):
        log(f'  {i+1:4d}| {lines[i]}')
else:
    log('  fetch_all.py tidak ditemukan')

# ══════════════════════════════════════════════════════
log('\n' + '='*60)
log('B. Coba numeric ID sebagai code (1-150)')
log('='*60)

valid_codes = []
for n in range(1, 151):
    code_val = str(n)
    time.sleep(0.15)
    try:
        r = requests.get(URL_TREK, headers=HEADERS,
                         params={'code': code_val}, timeout=6, verify=False)
        body = r.text.strip()[:120]
        is_valid = (r.status_code == 200 and
                    'tidak valid' not in body and
                    'Kode tidak' not in body and
                    'invalid' not in body.lower() and
                    'error' not in body.lower())
        if is_valid:
            log(f'  *** [{r.status_code}] code={code_val}  VALID! body={body}')
            valid_codes.append(code_val)
        elif n <= 10 or n % 25 == 0:
            # Tampilkan sample saja biar tidak terlalu panjang
            log(f'  [{r.status_code}] code={code_val:<5} {body}')
    except Exception as e:
        log(f'  [ERR] {n}: {e}')

log(f'\n  Numeric codes valid: {valid_codes}')

# ══════════════════════════════════════════════════════
log('\n' + '='*60)
log('C. Fetch halaman paito HK — cari data JS embedded')
log('='*60)

paito_urls = [
    f'{BASE}/paito-hk/',
    f'{BASE}/data-pengeluaran-togel-hongkong-pools/',
    f'{BASE}/data-pengeluaran-togel-hongkong/',
]
for pg_url in paito_urls:
    try:
        r = requests.get(pg_url, timeout=12, verify=False,
                         headers={**HEADERS, 'Accept': 'text/html'})
        if r.status_code != 200:
            log(f'  [{r.status_code}] {pg_url}')
            continue
        html = r.text
        log(f'  [200] {pg_url}  len={len(html):,}')

        # Cari semua data-* attributes
        data_attrs = re.findall(r'data-([a-z-]+)=["\']([^"\']{1,50})["\']', html)
        if data_attrs:
            log(f'    data-* attrs: {list(set(data_attrs))[:20]}')

        # Cari variabel JS yang berisi 'code'/'kode'/'pasaran'
        js_vars = re.findall(
            r'(?:var|let|const)\s+\w*(?:code|kode|pasaran|market)\w*\s*=\s*["\']([^"\']+)["\']',
            html, re.I
        )
        if js_vars:
            log(f'    JS vars: {js_vars[:10]}')

        # Cari inline JSON
        json_blobs = re.findall(r'\{[^<]{20,500}\}', html)
        for blob in json_blobs[:5]:
            if any(k in blob for k in ['"code"', '"kode"', '"pasaran"', 'bot-trek']):
                log(f'    JSON blob: {blob[:300]}')

        # Cari script src yang mungkin berisi config
        scripts = re.findall(r'<script[^>]+src=["\']([^"\']+premium[^"\']+)["\']', html)
        log(f'    Script srcs: {scripts[:5]}')

        # Cari nonce dan wpApiSettings
        api_settings = re.findall(r'wpApiSettings\s*=\s*(\{[^;]+\})', html)
        for s in api_settings:
            log(f'    wpApiSettings: {s[:300]}')

        if data_attrs or js_vars:
            break  # Cukup dari halaman pertama yang ada data
    except Exception as e:
        log(f'  [ERR] {pg_url}: {e}')

# ══════════════════════════════════════════════════════
log('\n' + '='*60)
log('D. Batch semua kode valid')
log('='*60)

if valid_codes:
    log(f'  ✓ Kode valid: {valid_codes}')
    try:
        r = requests.post(URL_BATCH, headers=HEADERS,
                          json={'codes': valid_codes, 'limit': 100},
                          timeout=20, verify=False)
        log(f'  [{r.status_code}] BATCH: {r.text[:3000]}')
    except Exception as e:
        log(f'  ERR: {e}')
else:
    log('  Tidak ada kode valid dari numeric 1-150.')
    log()
    log('  ═══ KESIMPULAN ═══')
    log('  Kode bot-trek BUKAN: slug URL, kode internal fetch_all, numeric ID 1-150')
    log('  Kemungkinan: UUID/hash atau kode di WP plugin database')
    log()
    log('  CARA PASTI dapat kode:')
    log('  1. Buka angkanet18.com di browser desktop')
    log('  2. Tekan F12 → tab Network')
    log('  3. Ketik "wla" di filter')
    log('  4. Refresh halaman / buka halaman paito')
    log('  5. Cari request ke /wla/v1/bot-trek')
    log('  6. Lihat tab Payload → catat nilai "code"')

with open('debug_api_v9.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('\n→ Saved to debug_api_v9.txt')
