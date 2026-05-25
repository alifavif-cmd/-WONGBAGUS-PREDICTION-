"""
debug_api.py v2 — Probe wla-premium-hub plugin & gateway-config
"""
import requests, json, re, time, urllib3
urllib3.disable_warnings()

BASE      = 'https://angkanet18.com'
DIRECT_IP = '159.65.133.131'
HEADERS = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'Accept': '*/*',
    'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8',
}
out = []
def log(s=''):
    print(s)
    out.append(str(s))

# ── 1. gateway-config.json ──
log('='*60)
log('1. /gateway-config.json')
log('='*60)
try:
    r = requests.get(f'{BASE}/gateway-config.json', headers=HEADERS, timeout=10, verify=False)
    log(f'HTTP {r.status_code}  len={len(r.text)}')
    log(r.text[:2000])
except Exception as e:
    log(f'ERROR: {e}')

# ── 2. WP REST API endpoints dari wla-premium-hub ──
log('\n' + '='*60)
log('2. WP-JSON routes dari plugin wla-premium-hub')
log('='*60)
try:
    r = requests.get(f'{BASE}/wp-json/', headers=HEADERS, timeout=15, verify=False)
    data = r.json()
    routes = data.get('routes', {})
    wla_routes = [k for k in routes if 'wla' in k.lower() or 'premium' in k.lower() or 'paito' in k.lower() or 'togel' in k.lower() or 'result' in k.lower()]
    log(f'Total routes: {len(routes)}')
    log(f'WLA/paito routes ({len(wla_routes)}):')
    for r2 in wla_routes:
        log(f'  {r2}')
    # Juga dump semua namespace
    namespaces = data.get('namespaces', [])
    log(f'\nNamespaces: {namespaces}')
except Exception as e:
    log(f'ERROR: {e}')

# ── 3. Probe plugin JS file untuk cari API endpoints ──
log('\n' + '='*60)
log('3. Analisis premium-hub.js')
log('='*60)
try:
    r = requests.get(
        f'{BASE}/wp-content/plugins/wla-premium-hub/app/framework/js/premium-hub.js',
        headers=HEADERS, timeout=15, verify=False
    )
    js = r.text
    log(f'HTTP {r.status_code}  len={len(js):,} chars')

    # Cari API endpoints dalam JS
    api_paths = re.findall(r'["\`](\/(?:wp-json|api|paito|result|data|get)[^"\'`\s]{3,})["\`]', js)
    if api_paths:
        log(f'\nAPI paths dalam JS:')
        for p in sorted(set(api_paths)): log(f'  {p}')

    # Cari fetch/axios calls
    fetches = re.findall(r'(?:fetch|axios\.(?:get|post))\s*\(\s*["`\']([^"`\']+)', js)
    if fetches:
        log(f'\nfetch/axios calls:')
        for f2 in set(fetches): log(f'  {f2}')

    # Cari socket events
    sockets = re.findall(r'\.(?:on|emit)\s*\(\s*["`\']([^"`\']+)', js)
    if sockets:
        log(f'\nSocket events:')
        for s2 in sorted(set(sockets))[:20]: log(f'  {s2}')

    # Dump 1000 char pertama
    log(f'\nJS preview (1000 char):')
    log(js[:1000])
except Exception as e:
    log(f'ERROR: {e}')

# ── 4. Probe Socket.IO server langsung ──
log('\n' + '='*60)
log('4. Probe Socket.IO / API server di port 3000')
log('='*60)
probe_urls = [
    f'http://{DIRECT_IP}:3000/',
    f'http://{DIRECT_IP}:3000/api/result/hk',
    f'http://{DIRECT_IP}:3000/api/paito/hk',
    f'http://{DIRECT_IP}:3000/result',
    f'http://{DIRECT_IP}:3000/paito',
    f'http://{DIRECT_IP}:3000/socket.io/?EIO=4&transport=polling',
]
for url in probe_urls:
    try:
        time.sleep(0.3)
        r = requests.get(url, headers=HEADERS, timeout=6, verify=False)
        ct = r.headers.get('content-type','')
        log(f'  {r.status_code} {url}  ct={ct[:30]}  len={len(r.text)}')
        if r.status_code == 200:
            log(f'    Preview: {r.text[:300]}')
    except Exception as e:
        log(f'  ERR {url}: {str(e)[:80]}')

# ── 5. Probe WP REST namespaces ──
log('\n' + '='*60)
log('5. Probe WP-JSON namespaces')
log('='*60)
ns_to_try = ['wla/v1', 'wla/v2', 'premium-hub/v1', 'paito/v1', 'togel/v1', 'angkanet/v1']
for ns in ns_to_try:
    try:
        time.sleep(0.3)
        r = requests.get(f'{BASE}/wp-json/{ns}/', headers=HEADERS, timeout=8, verify=False)
        log(f'  {r.status_code} /wp-json/{ns}/  len={len(r.text)}')
        if r.status_code == 200:
            log(f'    Preview: {r.text[:200]}')
    except Exception as e:
        log(f'  ERR /wp-json/{ns}/: {e}')

with open('debug_api.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('\n→ Saved to debug_api.txt')
