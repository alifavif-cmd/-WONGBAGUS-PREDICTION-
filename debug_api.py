"""
debug_api.py v8 — Dump definisi PASARAN dari fetch_all.py
fetch_all.py ditemukan len=32,208 — perlu cari blok PASARAN/MARKETS di dalamnya
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
log('A. Dump PASARAN list dari fetch_all.py')
log('='*60)

fa_source = ''
for sp in ['fetch_all.py', '/github/workspace/fetch_all.py']:
    if os.path.exists(sp):
        with open(sp, encoding='utf-8') as f:
            fa_source = f.read()
        log(f'  File: {sp}  len={len(fa_source):,}')
        break

if not fa_source:
    log('  fetch_all.py tidak ditemukan!')
else:
    lines = fa_source.splitlines()
    log(f'  Total lines: {len(lines)}')

    # ── Cari baris yang mengandung definisi pasaran ──
    keywords = ['PASARAN', 'MARKETS', 'pasaran', 'markets',
                'PASAR', 'togel', 'angkanet', 'data-pengeluaran',
                "'hk'", '"hk"', "'sgp'", '"sgp"',
                'hongkong', 'singapore', 'sydney']

    # Temukan baris-baris kunci
    key_lines = {}
    for i, line in enumerate(lines):
        for kw in keywords:
            if kw in line:
                key_lines[i] = line
                break

    log(f'\n  Baris yang mengandung keyword ({len(key_lines)} baris):')
    for lnum, ltext in sorted(key_lines.items())[:5]:
        log(f'    L{lnum+1}: {ltext[:120]}')

    # ── Cari blok definisi list/dict utama ──
    # Cari mulai dari baris pertama yang ada '[' atau '{' setelah keyword PASARAN
    pasaran_start = None
    for i, line in enumerate(lines):
        if re.search(r'(?:PASARAN|MARKETS?|pasar)\s*=\s*[\[\{]', line, re.I):
            pasaran_start = i
            log(f'\n  ✓ Definisi PASARAN ditemukan di baris {i+1}: {line[:100]}')
            break

    if pasaran_start is not None:
        # Dump 80 baris dari sana
        log('\n--- PASARAN definition (80 baris) ---')
        for i in range(pasaran_start, min(pasaran_start+80, len(lines))):
            log(f'  {i+1:4d}| {lines[i]}')
    else:
        # Tidak ketemu — dump dari baris pertama yang ada 'angkanet' / 'data-pengeluaran'
        log('\n  Definisi PASARAN tidak ketemu dengan pola biasa')
        log('  Cari baris pertama yang ada URL data-pengeluaran:')
        for i, line in enumerate(lines):
            if 'data-pengeluaran' in line or 'angkanet' in line.lower():
                start = max(0, i-5)
                log(f'\n--- Context sekitar baris {i+1} (60 baris) ---')
                for j in range(start, min(start+60, len(lines))):
                    log(f'  {j+1:4d}| {lines[j]}')
                break

    # ── Ekstrak semua URL data-pengeluaran ──
    log('\n--- Semua URL data-pengeluaran dalam fetch_all.py ---')
    urls = re.findall(r'https?://[^\s"\']+data-pengeluaran[^\s"\']+', fa_source)
    urls = list(dict.fromkeys(urls))
    log(f'  Total: {len(urls)}')
    for u in urls:
        slug_m = re.search(r'/data-pengeluaran-togel-([^/\s"\']+)', u)
        slug = slug_m.group(1) if slug_m else '?'
        log(f'  slug={slug:<35}  url={u}')

    # ── Ekstrak semua string 2-8 char yang kemungkinan kode ──
    # Cari pola: ('KODE', ...) atau {'kode': 'KODE', ...}
    code_patterns = re.findall(
        r'(?:kode|code)["\']?\s*[:=]\s*["\']([^"\']{2,20})["\']',
        fa_source, re.I
    )
    log(f'\n--- Pattern kode= ditemukan: {list(dict.fromkeys(code_patterns))} ---')

    # Cari tuple dengan 2 string
    tuples2 = re.findall(r'\(\s*["\']([^"\']{2,10})["\'],\s*["\']([^"\']{10,})["\']', fa_source)
    log(f'\n--- Tuple (pendek, panjang) — kemungkinan (kode, url): ---')
    for k, v in tuples2[:20]:
        log(f'    ({k!r}, {v[:60]!r})')

    # ── Dump baris 1-100 ──
    log('\n--- Lines 1-100 dari fetch_all.py ---')
    for i, line in enumerate(lines[:100]):
        log(f'  {i+1:4d}| {line}')

# ══════════════════════════════════════════════════════
log('\n' + '='*60)
log('B. Test kode dari hasil analisis (jika ada)')
log('='*60)

# Ambil slug dari URL yang ditemukan
test_codes = []
if fa_source:
    urls2 = re.findall(r'/data-pengeluaran-togel-([^/\s"\']+)', fa_source)
    test_codes = list(dict.fromkeys(urls2))
    log(f'  Kode dari URL ({len(test_codes)}): {test_codes}')

valid_codes = []
for code_val in test_codes:
    time.sleep(0.2)
    try:
        r = requests.get(URL_TREK, headers=HEADERS,
                         params={'code': code_val}, timeout=8, verify=False)
        body = r.text.strip()[:150]
        ok = 'tidak valid' not in body and 'error' not in body.lower()
        marker = '  ← ✓ VALID!' if ok and r.status_code==200 else ''
        log(f'  [{r.status_code}] {code_val:<35} {body}{marker}')
        if ok and r.status_code == 200:
            valid_codes.append(code_val)
    except Exception as e:
        log(f'  [ERR] {e}')

if valid_codes:
    log(f'\n  ✓ VALID CODES: {valid_codes}')
    r = requests.post(URL_BATCH, headers=HEADERS,
                      json={'codes': valid_codes}, timeout=20, verify=False)
    log(f'  BATCH [{r.status_code}]: {r.text[:2000]}')

with open('debug_api_v8.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('\n→ Saved to debug_api_v8.txt')
