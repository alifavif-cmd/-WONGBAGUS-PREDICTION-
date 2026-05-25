"""
debug_api.py v6 — Temuan v5:
  - bot-trek-batch struktur BENAR: {"status":"success","results":{<code>:{...}}}
  - Nilai code 'hk','sgp','sdy' masih invalid
  Strategi:
  1. Parse sitemap.xml → slug dari URL /data-pengeluaran-togel-XXX/
  2. Baca result.json (output fetch_all.py) → ambil field kode internal
  3. Coba semua slug ke bot-trek ?code= satu per satu
  4. Batch semua yang valid ke bot-trek-batch
"""
import requests, json, re, time, urllib3, os
from xml.etree import ElementTree as ET
urllib3.disable_warnings()

BASE    = 'https://angkanet18.com'
HEADERS = {
    'User-Agent'      : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept'          : '*/*',
    'Accept-Language' : 'id-ID,id;q=0.9,en;q=0.8',
    'Referer'         : 'https://angkanet18.com/',
}
URL_TREK  = f'{BASE}/wp-json/wla/v1/bot-trek'
URL_BATCH = f'{BASE}/wp-json/wla/v1/bot-trek-batch'

out = []
def log(s=''):
    print(s)
    out.append(str(s))

def safe_get(url, timeout=12):
    try:
        r = requests.get(url, headers=HEADERS, timeout=timeout, verify=False)
        return r
    except Exception as e:
        log(f'  [ERR] {url}: {e}')
        return None

# ══════════════════════════════════════════════════════
log('='*60)
log('A. Ekstrak kode dari sitemap.xml')
log('='*60)

slug_codes = []
sitemap_urls = [
    f'{BASE}/sitemap.xml',
    f'{BASE}/sitemap_index.xml',
    f'{BASE}/wp-sitemap.xml',
    f'{BASE}/wp-sitemap-posts-page-1.xml',
]

all_page_urls = []
for surl in sitemap_urls:
    r = safe_get(surl)
    if not r or r.status_code != 200:
        log(f'  [{r.status_code if r else "ERR"}] {surl}')
        continue
    log(f'  [200] {surl}  len={len(r.text)}')
    try:
        root = ET.fromstring(r.text)
        ns   = {'sm': 'http://www.sitemaps.org/schemas/sitemap/0.9'}
        # sitemap index → fetch child sitemaps
        for loc in root.findall('.//sm:loc', ns):
            url_val = loc.text.strip()
            if 'sitemap' in url_val:
                # child sitemap
                r2 = safe_get(url_val)
                if r2 and r2.status_code == 200:
                    root2 = ET.fromstring(r2.text)
                    for loc2 in root2.findall('.//sm:loc', ns):
                        all_page_urls.append(loc2.text.strip())
            else:
                all_page_urls.append(url_val)
    except Exception as e:
        # fallback: regex
        all_page_urls += re.findall(r'<loc>(https?://[^<]+)</loc>', r.text)
        log(f'  XML parse error, fallback regex: {e}')
    if all_page_urls:
        break

log(f'\n  Total URLs dari sitemap: {len(all_page_urls)}')

# Ekstrak slug dari URL /data-pengeluaran-togel-XXX/
togel_pages = [u for u in all_page_urls if 'data-pengeluaran' in u or 'togel' in u.lower()]
log(f'  URL togel/pengeluaran: {len(togel_pages)}')

for url in togel_pages[:5]:
    log(f'    {url}')
if len(togel_pages) > 5:
    log(f'    ... +{len(togel_pages)-5} lagi')

# Ekstrak slug
for url in togel_pages:
    m = re.search(r'/(?:data-pengeluaran-togel-|paito-)([^/]+)/?$', url)
    if m:
        slug = m.group(1).rstrip('/')
        slug_codes.append(slug)

slug_codes = list(dict.fromkeys(slug_codes))
log(f'\n  Slug codes dari sitemap ({len(slug_codes)}): {slug_codes[:40]}')

# ══════════════════════════════════════════════════════
log('\n' + '='*60)
log('B. Baca result.json (output fetch_all.py)')
log('='*60)

result_json_codes = []
result_paths = ['result.json', '/github/workspace/result.json']
for rp in result_paths:
    if os.path.exists(rp):
        try:
            with open(rp) as f:
                rdata = json.load(f)
            log(f'  result.json ditemukan: {rp}')
            log(f'  Type: {type(rdata).__name__}  len={len(rdata) if isinstance(rdata,(list,dict)) else "N/A"}')

            if isinstance(rdata, list):
                log(f'  Sample[0]: {json.dumps(rdata[0])[:300]}')
                # Ambil semua field yang mungkin berisi kode
                for item in rdata[:3]:
                    if isinstance(item, dict):
                        for k in ['code','kode','pasaran','market','slug','id']:
                            if k in item:
                                result_json_codes.append(str(item[k]))
                                log(f'    Field "{k}": {item[k]}')
            elif isinstance(rdata, dict):
                log(f'  Keys: {list(rdata.keys())[:20]}')
                log(f'  Preview: {json.dumps(rdata)[:500]}')
        except Exception as e:
            log(f'  Error baca {rp}: {e}')
    else:
        log(f'  {rp} tidak ada')

# ══════════════════════════════════════════════════════
log('\n' + '='*60)
log('C. Cek /wp-json/wla/v1/ untuk dokumentasi endpoint')
log('='*60)

r = safe_get(f'{BASE}/wp-json/wla/v1/')
if r and r.status_code == 200:
    log(f'  [200] len={len(r.text)}')
    log(f'  Body: {r.text[:2000]}')
    # Cari hint tentang valid codes
    if 'enum' in r.text or 'choices' in r.text or 'values' in r.text:
        log('  *** Ada enum/choices/values — cek body lengkap! ***')
else:
    log(f'  [{r.status_code if r else "ERR"}]')

# ══════════════════════════════════════════════════════
log('\n' + '='*60)
log('D. Brute-force bot-trek dengan slug dari sitemap')
log('='*60)

# Gabung semua kandidat
all_codes = list(dict.fromkeys(slug_codes + result_json_codes))

# Jika sitemap kosong, fallback ke derivasi manual dari nama pasaran umum
if not all_codes:
    log('  Sitemap kosong — pakai derivasi manual')
    base_names = [
        'hongkong','singapore','sydney','macau','taiwan',
        'tokyo','seoul','bangkok','kuala-lumpur','manila',
        'new-york','los-angeles','texas','florida','ohio',
        'georgia','carolina','virginia','tennessee','illinois',
        'michigan','kentucky','indiana','connecticut','maryland',
        'new-jersey','pennsylvania','massachusetts',
        'bulgaria','romania','slovakia','czech','austria',
    ]
    derivations = []
    for n in base_names:
        derivations += [
            n, n.replace('-','_'), n.replace('-',''),
            n + '-pools', n + '-prize', n + '-4d',
            n.upper(), n.upper().replace('-','_'),
        ]
    all_codes = list(dict.fromkeys(derivations))

log(f'  Total kandidat: {len(all_codes)}')

valid_codes = []
for code_val in all_codes:
    time.sleep(0.25)
    try:
        r = requests.get(URL_TREK, headers=HEADERS,
                         params={'code': code_val},
                         timeout=8, verify=False)
        body = r.text[:150]
        is_invalid = ('tidak valid' in body or
                      '"invalid"' in body.lower() or
                      'Kode tidak' in body)
        marker = '  ✓ VALID' if not is_invalid and r.status_code == 200 else ''
        log(f'  [{r.status_code}] code={code_val:<35} {body}{marker}')
        if marker:
            valid_codes.append(code_val)
    except Exception as e:
        log(f'  [ERR] {code_val}: {e}')

# ══════════════════════════════════════════════════════
log('\n' + '='*60)
log('E. Batch fetch dengan kode valid')
log('='*60)

if valid_codes:
    log(f'  KODE VALID: {valid_codes}')
    # Fetch semua sekaligus
    try:
        r = requests.post(URL_BATCH, headers=HEADERS,
                          json={'codes': valid_codes},
                          timeout=15, verify=False)
        log(f'  [{r.status_code}] POST batch all valid codes')
        log(f'  len={len(r.text)}')
        log(f'  body={r.text[:2000]}')
    except Exception as e:
        log(f'  ERR: {e}')

    # Juga coba dengan limit
    try:
        r = requests.post(URL_BATCH, headers=HEADERS,
                          json={'codes': valid_codes, 'limit': 100},
                          timeout=15, verify=False)
        log(f'\n  [{r.status_code}] POST batch + limit=100')
        log(f'  body={r.text[:2000]}')
    except Exception as e:
        log(f'  ERR: {e}')
else:
    log('  Tidak ada kode valid ditemukan.')
    log()
    log('  === ANALISIS FINAL ===')
    log('  Kemungkinan kode valid berasal dari:')
    log('  1. Database internal plugin (perlu login WP admin)')
    log('  2. Format kode yang sama dengan fetch_all.py (perlu cek source)')
    log('  3. Endpoint /wla/v1/app yang perlu auth')
    log()
    log('  Coba: buka DevTools di angkanet18.com, tab Network,')
    log('  filter "wla", lalu trigger refresh paito — lihat request bot-trek.')

# Simpan
with open('debug_api_v6.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('\n→ Saved to debug_api_v6.txt')
