"""
debug_api.py v3 — Fokus probe /wla/v1/bot-trek & bot-trek-batch
Temuan v2:
  - active_domain: https://159.65.133.131/
  - /wla/v1/bot-trek       ← mungkin single fetch
  - /wla/v1/bot-trek-batch ← mungkin bulk/historical fetch
"""
import requests, json, time, urllib3
urllib3.disable_warnings()

BASE      = 'https://angkanet18.com'
DIRECT_IP = 'https://159.65.133.131'   # active_domain dari gateway-config
HEADERS = {
    'User-Agent'      : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept'          : 'application/json, */*',
    'Accept-Language' : 'id-ID,id;q=0.9,en;q=0.8',
    'Referer'         : 'https://angkanet18.com/',
}

out = []
def log(s=''):
    print(s)
    out.append(str(s))

def probe(label, url, method='GET', params=None, body=None, extra_headers=None):
    """Helper: coba satu request, log hasilnya."""
    h = {**HEADERS, **(extra_headers or {})}
    try:
        time.sleep(0.4)
        if method == 'POST':
            r = requests.post(url, headers=h, params=params,
                              json=body, timeout=10, verify=False)
        else:
            r = requests.get(url, headers=h, params=params,
                             timeout=10, verify=False)
        ct = r.headers.get('content-type', '')
        log(f'  [{r.status_code}] {label}')
        log(f'        URL    : {r.url}')
        log(f'        CT     : {ct[:60]}')
        log(f'        len    : {len(r.text)}')
        if r.status_code == 200 and r.text.strip():
            log(f'        Preview: {r.text[:400]}')
        elif r.status_code != 200:
            log(f'        Body   : {r.text[:200]}')
    except Exception as e:
        log(f'  [ERR] {label}: {str(e)[:100]}')
    log()

# ═══════════════════════════════════════════════════
log('='*60)
log('A. bot-trek  — GET dengan berbagai kombinasi param')
log('='*60)

# Kandidat nama param pasaran
PASARAN_KEYS   = ['pasaran', 'market', 'code', 'slug', 'id', 'name']
PASARAN_VALUES = ['hk', 'hongkong', 'hkg', 'HK', 'HONGKONG']

for base_url in [f'{BASE}/wp-json/wla/v1/bot-trek',
                 f'{DIRECT_IP}/wp-json/wla/v1/bot-trek']:
    log(f'\n--- {base_url} ---')

    # Tanpa param
    probe('no params', base_url)

    # Coba semua kombinasi key=value
    for key in PASARAN_KEYS:
        for val in PASARAN_VALUES[:2]:   # hk & hongkong saja biar tidak terlalu banyak
            probe(f'{key}={val}', base_url, params={key: val})

    # Tambahan: dengan limit/count/hist
    probe('pasaran=hk&limit=10', base_url,
          params={'pasaran': 'hk', 'limit': 10})
    probe('pasaran=hk&count=30', base_url,
          params={'pasaran': 'hk', 'count': 30})
    probe('pasaran=hk&hist=1',   base_url,
          params={'pasaran': 'hk', 'hist': 1})

# ═══════════════════════════════════════════════════
log('='*60)
log('B. bot-trek  — POST dengan JSON body')
log('='*60)

bodies_trek = [
    {'pasaran': 'hk'},
    {'market' : 'hk'},
    {'code'   : 'hk'},
    {'pasaran': 'hk', 'limit': 30},
    {'pasaran': 'hk', 'action': 'get'},
    {'pasaran': 'hk', 'type'  : 'result'},
]
for base_url in [f'{BASE}/wp-json/wla/v1/bot-trek',
                 f'{DIRECT_IP}/wp-json/wla/v1/bot-trek']:
    log(f'\n--- POST {base_url} ---')
    for body in bodies_trek:
        probe(f'POST {body}', base_url, method='POST', body=body)

# ═══════════════════════════════════════════════════
log('='*60)
log('C. bot-trek-batch  — GET berbagai param')
log('='*60)

BATCH_PARAMS = [
    {},
    {'pasaran': 'hk'},
    {'pasaran': 'hk', 'limit' : 100},
    {'pasaran': 'hk', 'count' : 100},
    {'pasaran': 'hk', 'period': 30},
    {'pasaran': 'hk', 'days'  : 30},
    {'pasaran': 'hk', 'page'  : 1},
    {'pasaran': 'hk', 'from'  : '2026-01-01', 'to': '2026-05-25'},
    {'markets' : 'hk,sgp,sdy'},   # mungkin multi-pasaran
    {'batch'   : 1},
    {'all'     : 1},
]
for base_url in [f'{BASE}/wp-json/wla/v1/bot-trek-batch',
                 f'{DIRECT_IP}/wp-json/wla/v1/bot-trek-batch']:
    log(f'\n--- {base_url} ---')
    for p in BATCH_PARAMS:
        probe(f'GET {p}', base_url, params=p if p else None)

# ═══════════════════════════════════════════════════
log('='*60)
log('D. bot-trek-batch  — POST JSON body')
log('='*60)

bodies_batch = [
    {'pasaran': 'hk'},
    {'pasaran': 'hk', 'limit' : 100},
    {'pasarans': ['hk', 'sgp', 'sdy']},
    {'markets'  : ['hk', 'sgp']},
    {'action'   : 'batch', 'pasaran': 'hk'},
    {'type'     : 'all'},
]
for base_url in [f'{BASE}/wp-json/wla/v1/bot-trek-batch',
                 f'{DIRECT_IP}/wp-json/wla/v1/bot-trek-batch']:
    log(f'\n--- POST {base_url} ---')
    for body in bodies_batch:
        probe(f'POST {body}', base_url, method='POST', body=body)

# ═══════════════════════════════════════════════════
log('='*60)
log('E. Endpoint saudara — pwa-track & pwa-stats (GET)')
log('='*60)

sibling_endpoints = [
    '/wp-json/wla/v1/app',
    '/wp-json/wla/v1/pwa-track',
    '/wp-json/wla/v1/pwa-stats',
]
for ep in sibling_endpoints:
    for base_url in [BASE, DIRECT_IP]:
        probe(f'{base_url}{ep}', f'{base_url}{ep}')
        probe(f'{base_url}{ep} pasaran=hk',
              f'{base_url}{ep}', params={'pasaran': 'hk'})

# ═══════════════════════════════════════════════════
log('='*60)
log('F. Coba WP nonce / auth header (kalau butuh login)')
log('='*60)

# Beberapa plugin WP pakai X-WP-Nonce atau Bearer token
# Coba dulu tanpa auth — kalau 401/403, perlu login dulu
r_check = None
try:
    r_check = requests.get(
        f'{BASE}/wp-json/wla/v1/bot-trek-batch',
        headers={**HEADERS, 'X-WP-Nonce': 'test'},
        timeout=8, verify=False
    )
    log(f'  With X-WP-Nonce: {r_check.status_code}  {r_check.text[:200]}')
except Exception as e:
    log(f'  ERR: {e}')

# Simpan hasil
with open('debug_api_v3.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('\n→ Saved to debug_api_v3.txt')
