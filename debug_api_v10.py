"""
debug_api.py v10 — Pendekatan terakhir:
  OPTIONS method ke bot-trek → WP REST wajib return schema + enum
  Juga: dump full /wp-json/wla/v1/ routes + coba akses PHP plugin
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

def req(method, url, **kwargs):
    try:
        r = requests.request(method, url, headers=HEADERS,
                             timeout=12, verify=False, **kwargs)
        return r
    except Exception as e:
        log(f'  [ERR {method} {url}]: {e}')
        return None

# ══════════════════════════════════════════════════════
log('='*60)
log('A. OPTIONS request — ambil schema enum dari WP REST')
log('='*60)

for url in [URL_TREK, URL_BATCH,
            f'{BASE}/wp-json/wla/v1/',
            f'{BASE}/wp-json/wla/v1/pwa-track',
            f'{BASE}/wp-json/wla/v1/pwa-stats']:
    r = req('OPTIONS', url)
    if not r:
        continue
    log(f'\n  OPTIONS {url}')
    log(f'  Status : {r.status_code}')
    log(f'  Allow  : {r.headers.get("Allow", "-")}')
    log(f'  len    : {len(r.text)}')
    # Dump full body — schema ada di sini
    log(f'  Body   : {r.text[:3000]}')

    # Parse JSON — cari enum/values untuk param 'code'
    try:
        schema = r.json()
        # Cari key enum/choices/values di seluruh schema
        raw = json.dumps(schema)
        if 'enum' in raw or 'choices' in raw:
            log(f'\n  *** ENUM/CHOICES DITEMUKAN! ***')
            # Cari semua enum arrays
            enums = re.findall(r'"enum"\s*:\s*(\[[^\]]+\])', raw)
            for e in enums:
                log(f'    enum: {e[:500]}')
        # Cari args untuk parameter code
        args = schema.get('schema', {}).get('properties', {})
        if 'code' in args:
            log(f'  code param schema: {json.dumps(args["code"])[:500]}')
        if 'codes' in args:
            log(f'  codes param schema: {json.dumps(args["codes"])[:500]}')
    except:
        pass

# ══════════════════════════════════════════════════════
log('\n' + '='*60)
log('B. Dump semua routes dari /wp-json/ yang relate ke wla')
log('='*60)

r = req('GET', f'{BASE}/wp-json/')
if r and r.status_code == 200:
    try:
        data = r.json()
        routes = data.get('routes', {})
        # Filter wla routes
        wla = {k: v for k, v in routes.items() if 'wla' in k.lower()}
        log(f'  WLA routes: {len(wla)}')
        for route, info in wla.items():
            log(f'\n  Route: {route}')
            # Dump endpoints + args
            for ep in info.get('endpoints', []):
                log(f'    Methods: {ep.get("methods")}')
                args = ep.get('args', {})
                for arg_name, arg_info in args.items():
                    log(f'    Arg "{arg_name}": {json.dumps(arg_info)[:300]}')
    except Exception as e:
        log(f'  Parse error: {e}')
        log(f'  Raw: {r.text[:1000]}')

# ══════════════════════════════════════════════════════
log('\n' + '='*60)
log('C. Akses file PHP plugin langsung')
log('='*60)

php_files = [
    '/wp-content/plugins/wla-premium-hub/wla-premium-hub.php',
    '/wp-content/plugins/wla-premium-hub/app/framework/php/bot-trek.php',
    '/wp-content/plugins/wla-premium-hub/app/framework/php/api.php',
    '/wp-content/plugins/wla-premium-hub/includes/api.php',
    '/wp-content/plugins/wla-premium-hub/api/bot-trek.php',
    '/wp-content/plugins/wla-premium-hub/app/api.php',
]
for path in php_files:
    r = req('GET', f'{BASE}{path}')
    if not r:
        continue
    log(f'  [{r.status_code}] {path}  len={len(r.text)}')
    if r.status_code == 200 and r.text.strip():
        log(f'    Preview: {r.text[:500]}')
        # Cari kode pasaran dalam PHP
        codes_in_php = re.findall(r'["\']([a-z0-9_-]{2,15})["\']', r.text)
        freq = {}
        for c in codes_in_php:
            freq[c] = freq.get(c, 0) + 1
        top = [(c,n) for c,n in sorted(freq.items(),key=lambda x:-x[1]) if n>=3]
        log(f'    Top strings: {top[:20]}')

# ══════════════════════════════════════════════════════
log('\n' + '='*60)
log('D. Coba slug URL dari fetch_all PASARAN dict ke bot-trek')
log('='*60)

# Dari image v9: PASARAN dict internal codes
fa_internal = {
    'hk': 'hongkong-pools', 'hkl': 'hklotto', 'sgp': 'singapore',
    'sdy': 'sydneypools', 'sdl': 'sdlotto', 'kam': 'magnum-cambodia',
    'bull': 'bullseye', 'chn': 'chinapools', 'twn': 'taiwan',
    'jpn': 'japan',
}
# Coba berbagai derivasi
derived = []
for internal, slug in fa_internal.items():
    derived += [
        internal, slug,
        internal.upper(), slug.upper(),
        slug.replace('-','_'), slug.replace('-',''),
        internal + '_pools', internal + '-pools',
        slug.split('-')[0],  # kata pertama slug
    ]
derived = list(dict.fromkeys(derived))

log(f'  Kandidat ({len(derived)}): {derived}')
valid = []
for c in derived:
    time.sleep(0.2)
    r = req('GET', URL_TREK, params={'code': c})
    if not r: continue
    body = r.text.strip()[:120]
    ok = r.status_code==200 and 'tidak valid' not in body and 'error' not in body.lower()
    marker = '  ← VALID!' if ok else ''
    log(f'  [{r.status_code}] {c:<25} {body}{marker}')
    if ok: valid.append(c)

# ══════════════════════════════════════════════════════
log('\n' + '='*60)
log('E. Coba akses langsung ke WP database via phpMyAdmin / WP CLI')
log('   (hanya jika ada endpoint admin yang terbuka)')
log('='*60)

admin_probes = [
    f'{BASE}/wp-admin/admin-ajax.php',
    f'{BASE}/wp-json/wla/v1/bot-trek?action=list',
    f'{BASE}/wp-json/wla/v1/bot-trek?action=codes',
    f'{BASE}/wp-json/wla/v1/bot-trek?list=1',
    f'{BASE}/wp-json/wla/v1/bot-trek?all=1',
]
for url in admin_probes:
    r = req('GET', url)
    if not r: continue
    log(f'  [{r.status_code}] {url}')
    log(f'    {r.text[:200]}')

if valid:
    log(f'\n✓ VALID CODES: {valid}')
    r = req('POST', URL_BATCH, json={'codes': valid, 'limit': 100})
    if r: log(f'BATCH: [{r.status_code}] {r.text[:2000]}')
else:
    log('\n═══ REKOMENDASI FINAL ═══')
    log('bot-trek codes tidak bisa ditemukan via scripting.')
    log('Cara tercepat: DevTools browser → Network → filter wla')
    log('Atau: gunakan fetch_all.py yang sudah berjalan dengan baik (64/64 pasaran).')

with open('debug_api_v10.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('\n→ Saved to debug_api_v10.txt')
