"""
debug_api.py v4 — Temuan v3:
  - bot-trek butuh param  : code  ATAU  codes
  - pwa-stats/pwa-track   : 403 Unauthorized (butuh nonce)
  - Nonce strategy        : scrape dari halaman frontend angkanet18.com
"""
import requests, json, re, time, urllib3
urllib3.disable_warnings()

BASE    = 'https://angkanet18.com'
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

def probe(label, url, method='GET', params=None, body=None, headers_extra=None):
    h = {**HEADERS, **(headers_extra or {})}
    try:
        time.sleep(0.4)
        if method == 'POST':
            r = requests.post(url, headers=h, params=params,
                              json=body, timeout=10, verify=False)
        else:
            r = requests.get(url, headers=h, params=params,
                             timeout=10, verify=False)
        log(f'  [{r.status_code}] {label}')
        log(f'        len={len(r.text)}  body={r.text[:300]}')
    except Exception as e:
        log(f'  [ERR] {label}: {str(e)[:120]}')
    log()

# ═══════════════════════════════════════════════════════
log('='*60)
log('A. bot-trek — param "code" dan "codes" (temuan v3)')
log('='*60)

URL_TREK  = f'{BASE}/wp-json/wla/v1/bot-trek'
URL_BATCH = f'{BASE}/wp-json/wla/v1/bot-trek-batch'

# Kode pasaran yang umum dipakai
CODES_SINGLE = ['hk', 'HK', 'hongkong', 'hkg',
                 'sgp', 'sdy', 'macau', 'taiwan']
CODES_MULTI  = 'hk,sgp,sdy,macau'

log('\n--- GET bot-trek ?code=X ---')
for c in CODES_SINGLE:
    probe(f'code={c}', URL_TREK, params={'code': c})

log('\n--- GET bot-trek ?codes=X ---')
for c in CODES_SINGLE[:4]:
    probe(f'codes={c}', URL_TREK, params={'codes': c})

log('\n--- GET bot-trek ?codes=multi ---')
probe('codes=hk,sgp,sdy,macau', URL_TREK, params={'codes': CODES_MULTI})

log('\n--- GET bot-trek dengan limit/hist ---')
for extra in [{'limit':30}, {'limit':100}, {'hist':1},
              {'hist':30}, {'count':30}, {'page':1}]:
    probe(f'code=hk + {extra}', URL_TREK,
          params={'code': 'hk', **extra})

log('\n--- POST bot-trek body code/codes ---')
bodies = [
    {'code' : 'hk'},
    {'codes': 'hk'},
    {'codes': ['hk']},
    {'code' : 'hk', 'limit': 100},
    {'codes': 'hk,sgp,sdy'},
    {'codes': ['hk','sgp','sdy']},
]
for b in bodies:
    probe(f'POST {b}', URL_TREK, method='POST', body=b)

# ═══════════════════════════════════════════════════════
log('='*60)
log('B. bot-trek-batch — param "code" dan "codes"')
log('='*60)

log('\n--- GET bot-trek-batch ---')
for c in CODES_SINGLE[:4]:
    probe(f'code={c}', URL_BATCH, params={'code': c})
    probe(f'codes={c}', URL_BATCH, params={'codes': c})

probe('codes=multi', URL_BATCH, params={'codes': CODES_MULTI})
probe('code=hk&limit=100', URL_BATCH, params={'code':'hk','limit':100})
probe('code=hk&hist=30',   URL_BATCH, params={'code':'hk','hist':30})
probe('codes=hk&all=1',    URL_BATCH, params={'codes':'hk','all':1})

log('\n--- POST bot-trek-batch ---')
batch_bodies = [
    {'code' : 'hk'},
    {'codes': 'hk'},
    {'codes': ['hk']},
    {'code' : 'hk', 'limit': 200},
    {'codes': ['hk','sgp','sdy','macau','taiwan']},
    {'code' : 'hk', 'hist': 100},
]
for b in batch_bodies:
    probe(f'POST {b}', URL_BATCH, method='POST', body=b)

# ═══════════════════════════════════════════════════════
log('='*60)
log('C. Auto-extract WP Nonce dari halaman frontend')
log('='*60)

nonce = None
nonce_sources = [
    BASE + '/',
    BASE + '/paito-hk/',
    BASE + '/data-pengeluaran-togel-hongkong/',
]

for page_url in nonce_sources:
    if nonce:
        break
    try:
        r = requests.get(page_url, headers={**HEADERS, 'Accept': 'text/html'},
                         timeout=12, verify=False)
        html = r.text

        # Pola umum WP nonce dalam inline JS
        patterns = [
            r'["\']nonce["\']\s*:\s*["\']([a-f0-9]{10,})["\']',
            r'nonce\s*=\s*["\']([a-f0-9]{10,})["\']',
            r'wpApiSettings[^}]*nonce["\']?\s*:\s*["\']([a-f0-9]{10,})["\']',
            r'rest_nonce["\']?\s*:\s*["\']([a-f0-9]{10,})["\']',
            r'X-WP-Nonce["\']?\s*:\s*["\']([a-f0-9]{10,})["\']',
            r'wlaNonce\s*[=:]\s*["\']([a-f0-9]{10,})["\']',
            r'premiumNonce\s*[=:]\s*["\']([a-f0-9]{10,})["\']',
        ]
        for pat in patterns:
            m = re.search(pat, html, re.IGNORECASE)
            if m:
                nonce = m.group(1)
                log(f'  ✓ Nonce ditemukan di {page_url}')
                log(f'    Pattern : {pat[:60]}')
                log(f'    Nonce   : {nonce}')
                break

        if not nonce:
            # Dump semua string yang mirip nonce (10 hex chars)
            candidates = re.findall(r'[a-f0-9]{10,12}', html)
            unique_cand = list(dict.fromkeys(candidates))[:10]
            log(f'  {page_url} — nonce tidak ditemukan')
            log(f'    Kandidat hex: {unique_cand}')

            # Cek apakah ada wp-json settings di inline script
            if 'wpApiSettings' in html or 'rest_url' in html:
                snippet_idx = html.find('wpApiSettings')
                if snippet_idx == -1:
                    snippet_idx = html.find('rest_url')
                log(f'    wpApiSettings snippet: {html[snippet_idx:snippet_idx+300]}')

    except Exception as e:
        log(f'  ERR {page_url}: {e}')

log()

# ═══════════════════════════════════════════════════════
log('='*60)
log('D. Pakai nonce (jika berhasil dapat) ke endpoint protected')
log('='*60)

if nonce:
    nonce_header = {'X-WP-Nonce': nonce}
    log(f'Menggunakan nonce: {nonce}')
    log()

    protected = [
        (URL_TREK,  {'code':'hk'}),
        (URL_BATCH, {'code':'hk'}),
        (URL_BATCH, {'codes':'hk,sgp,sdy'}),
        (f'{BASE}/wp-json/wla/v1/pwa-stats',  {'code':'hk'}),
        (f'{BASE}/wp-json/wla/v1/pwa-track',  {'code':'hk'}),
    ]
    for url, p in protected:
        probe(f'{url.split("/")[-1]} + nonce',
              url, params=p, headers_extra=nonce_header)

    # Juga coba POST dengan nonce
    probe('POST bot-trek-batch + nonce',
          URL_BATCH, method='POST',
          body={'codes':['hk','sgp','sdy']},
          headers_extra=nonce_header)
else:
    log('  Nonce tidak berhasil di-extract — coba manual:')
    log('  1. Buka angkanet18.com di browser')
    log('  2. DevTools → Console → ketik:')
    log('       copy(wpApiSettings.nonce)')
    log('  3. Paste nilai nonce ke script ini secara manual')

# ═══════════════════════════════════════════════════════
log('='*60)
log('E. Coba endpoint bot-trek dengan cookie session')
log('='*60)

# Jika ada akun, bisa set cookie PHPSESSID / wordpress_logged_in_xxx di sini
# Untuk sekarang: coba request dengan Accept: text/html untuk bypass JSON auth check
probe('bot-trek HTML accept',
      URL_TREK, params={'code':'hk'},
      headers_extra={'Accept': 'text/html,application/xhtml+xml'})

probe('bot-trek-batch HTML accept',
      URL_BATCH, params={'code':'hk'},
      headers_extra={'Accept': 'text/html,application/xhtml+xml'})

# Simpan
with open('debug_api_v4.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('\n→ Saved to debug_api_v4.txt')
