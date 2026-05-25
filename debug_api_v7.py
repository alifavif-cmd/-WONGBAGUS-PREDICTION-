"""
debug_api.py v7 — Baca fetch_all.py → ekstrak kode pasaran → probe bot-trek-batch
Insight: fetch_all.py sudah berhasil fetch 64 pasaran, pasti ada mapping kode di sana.
"""
import requests, json, re, time, urllib3, os, ast
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
log('A. Baca fetch_all.py — ekstrak semua kode & URL pasaran')
log('='*60)

fetch_all_codes   = []   # kode internal (HK, SGP, dll)
fetch_all_slugs   = []   # slug URL (data-pengeluaran-togel-XXX)

# Cari file di berbagai lokasi
search_paths = [
    'fetch_all.py',
    '/github/workspace/fetch_all.py',
    os.path.join(os.path.dirname(__file__), 'fetch_all.py'),
]

fa_source = None
for sp in search_paths:
    try:
        if os.path.exists(sp):
            with open(sp, encoding='utf-8') as f:
                fa_source = f.read()
            log(f'  ✓ fetch_all.py ditemukan: {sp}  len={len(fa_source):,}')
            break
    except Exception as e:
        log(f'  ERR baca {sp}: {e}')

if not fa_source:
    log('  fetch_all.py tidak ditemukan di lokasi manapun')
else:
    # ── Tampilkan 3000 char pertama ──
    log('\n--- Source preview (3000 char) ---')
    log(fa_source[:3000])
    log('...')

    # ── Ekstrak semua string literal yang ada 'togel' atau kode pasaran ──
    # Pola: dict/list berisi pasaran
    # Cari definisi list/dict pasaran
    
    # 1. Pola: {'kode': 'XXX', 'url': '...'}
    dicts = re.findall(
        r'\{[^{}]*(?:kode|code|pasaran|market|slug)[^{}]*\}',
        fa_source, re.IGNORECASE | re.DOTALL
    )
    log(f'\n  Dict patterns ditemukan: {len(dicts)}')
    for d in dicts[:10]:
        log(f'    {d[:200]}')
        # Coba parse
        kode_m = re.search(r'["\'](?:kode|code|pasaran)["\']:\s*["\']([^"\']+)["\']', d, re.I)
        url_m  = re.search(r'["\'](?:url|link|href)["\']:\s*["\']([^"\']+)["\']', d, re.I)
        if kode_m:
            fetch_all_codes.append(kode_m.group(1))
        if url_m:
            slug_m = re.search(r'/data-pengeluaran-togel-([^/]+)/?', url_m.group(1))
            if slug_m:
                fetch_all_slugs.append(slug_m.group(1))

    # 2. Pola: tuple ('XXX', 'https://...')
    tuples = re.findall(
        r'\(\s*["\']([A-Z]{2,6})["\'],\s*["\']([^"\']+togel[^"\']+)["\']',
        fa_source
    )
    log(f'\n  Tuple (kode, url) ditemukan: {len(tuples)}')
    for code_t, url_t in tuples[:10]:
        log(f'    ({code_t}, {url_t})')
        fetch_all_codes.append(code_t)
        slug_m = re.search(r'/data-pengeluaran-togel-([^/]+)/?', url_t)
        if slug_m:
            fetch_all_slugs.append(slug_m.group(1))

    # 3. Pola: PASARAN = [...] atau MARKETS = [...]
    list_defs = re.findall(
        r'(?:PASARAN|MARKETS?|CODES?|LIST)\s*=\s*\[([^\]]+)\]',
        fa_source, re.IGNORECASE | re.DOTALL
    )
    log(f'\n  List definitions ditemukan: {len(list_defs)}')
    for ld in list_defs:
        log(f'    {ld[:300]}')

    # 4. Semua URL data-pengeluaran di source
    urls_in_source = re.findall(
        r'https?://[^"\']+/data-pengeluaran-togel-([^/"\']+)/?',
        fa_source
    )
    log(f'\n  URL slugs dalam source ({len(urls_in_source)}): {list(dict.fromkeys(urls_in_source))}')
    fetch_all_slugs.extend(urls_in_source)

    # 5. Semua string CAPSLOCK pendek (kemungkinan kode)
    caps_codes = re.findall(r'\b([A-Z]{2,6})\b', fa_source)
    freq = {}
    for c in caps_codes:
        freq[c] = freq.get(c, 0) + 1
    ignore_caps = {'HTTP','URL','GET','POST','CSS','HTML','JSON','API',
                   'WP','ID','OK','FOR','IF','IN','OR','AND','NOT','IS',
                   'TRUE','FALSE','NONE','UTF','SSL','NCE','BF','GEOM',
                   'GEOE','HK','SGP','SDY','MAC','TWN','SHG','BJ','TW'}
    cap_candidates = [(c, n) for c, n in sorted(freq.items(), key=lambda x:-x[1])
                      if n >= 2 and c not in ignore_caps]
    log(f'\n  CAPS codes (freq≥2): {cap_candidates[:30]}')
    fetch_all_codes.extend([c for c,_ in cap_candidates[:20]])

    # 6. Cek juga kode dalam comment/konfigurasi
    comments = re.findall(r'#.*(?:kode|code|pasaran).*', fa_source, re.I)
    for cm in comments[:10]:
        log(f'  Comment: {cm}')

# ══════════════════════════════════════════════════════
log('\n' + '='*60)
log('B. Baca result.json — lihat struktur data yang sudah ada')
log('='*60)

result_codes = []
result_path = 'result.json'
if os.path.exists(result_path):
    with open(result_path, encoding='utf-8') as f:
        rdata = json.load(f)
    log(f'  result.json ada, type={type(rdata).__name__}')
    if isinstance(rdata, list) and rdata:
        log(f'  len={len(rdata)}  sample[0]={json.dumps(rdata[0])[:500]}')
        log(f'  sample[1]={json.dumps(rdata[1])[:300] if len(rdata)>1 else ""}')
        # Ekstrak semua key
        keys = set()
        for item in rdata:
            if isinstance(item, dict):
                keys.update(item.keys())
        log(f'  All keys: {sorted(keys)}')
        # Ambil kode
        for item in rdata:
            if isinstance(item, dict):
                for k in ['code','kode','pasaran','market','id','slug']:
                    if k in item:
                        result_codes.append(str(item[k]))
    elif isinstance(rdata, dict):
        log(f'  Keys: {list(rdata.keys())[:30]}')
        log(f'  Preview: {json.dumps(rdata)[:1000]}')
else:
    log('  result.json tidak ditemukan')

# ══════════════════════════════════════════════════════
log('\n' + '='*60)
log('C. Susun semua kandidat & test ke bot-trek')
log('='*60)

# Deduplikasi
all_candidates = list(dict.fromkeys(
    fetch_all_codes + fetch_all_slugs + result_codes
))

# Tambah variasi dari slug sitemap yang belum dicoba
extra = []
for slug in ['hongkong-pools','sydneypools','singapore','taiwan',
             'chinapools','japan','magnum-cambodia','sdlotto','hklotto']:
    # Coba variasi transformasi
    extra += [
        slug,
        slug.replace('-','_'),
        slug.replace('-','').replace('pools','').replace('lotto',''),
        slug.upper(),
        slug.upper().replace('-','_'),
        slug.split('-')[0],  # ambil kata pertama saja
    ]
all_candidates = list(dict.fromkeys(all_candidates + extra))

log(f'  Total kandidat: {len(all_candidates)}')
log(f'  Preview: {all_candidates[:50]}')
log()

valid_codes = []
for code_val in all_candidates:
    time.sleep(0.25)
    try:
        r = requests.get(URL_TREK, headers=HEADERS,
                         params={'code': code_val}, timeout=8, verify=False)
        body = r.text.strip()[:200]
        is_valid = (r.status_code == 200 and
                    'tidak valid' not in body and
                    'invalid' not in body.lower() and
                    'error' not in body.lower())
        marker = '  ← ✓ VALID!' if is_valid else ''
        log(f'  [{r.status_code}] code={code_val:<30}  {body}{marker}')
        if is_valid:
            valid_codes.append(code_val)
    except Exception as e:
        log(f'  [ERR] {code_val}: {e}')

# ══════════════════════════════════════════════════════
log('\n' + '='*60)
log('D. Batch semua kode valid')
log('='*60)

if valid_codes:
    log(f'  ✓ Kode valid: {valid_codes}')
    try:
        r = requests.post(URL_BATCH, headers=HEADERS,
                          json={'codes': valid_codes},
                          timeout=20, verify=False)
        log(f'  [{r.status_code}] POST batch')
        log(f'  len={len(r.text)}')
        log(r.text[:3000])
    except Exception as e:
        log(f'  ERR: {e}')
else:
    log('  Tidak ada kode valid — kode mungkin di-generate sisi server.')
    log()
    log('  REKOMENDASI TERAKHIR:')
    log('  Buka angkanet18.com → F12/DevTools → Network tab')
    log('  Filter: wla')
    log('  Klik/buka halaman paito manapun')
    log('  Cari request ke /wla/v1/bot-trek → lihat param "code"')
    log('  Paste kode itu ke sini.')

with open('debug_api_v7.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('\n→ Saved to debug_api_v7.txt')
