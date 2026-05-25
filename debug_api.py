"""
debug_api.py v5 — Temuan v4:
  - param 'code' benar, tapi nilainya salah ("Kode tidak valid / hk")
  - bot-trek-batch butuh 'codes[]' bukan 'codes'
  Strategi:
  1. Ambil daftar kode valid dari /wla/v1/app + JS plugin
  2. Coba kode yang ditemukan ke bot-trek & bot-trek-batch
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

def get(url, params=None, accept_html=False):
    h = {**HEADERS}
    if accept_html:
        h['Accept'] = 'text/html,application/xhtml+xml'
    try:
        r = requests.get(url, headers=h, params=params, timeout=12, verify=False)
        return r
    except Exception as e:
        log(f'  [ERR GET {url}]: {e}')
        return None

def probe(label, url, method='GET', params=None, body=None, hx=None):
    h = {**HEADERS, **(hx or {})}
    try:
        time.sleep(0.35)
        if method == 'POST':
            r = requests.post(url, headers=h, params=params,
                              json=body, timeout=10, verify=False)
        else:
            r = requests.get(url, headers=h, params=params,
                             timeout=10, verify=False)
        status = r.status_code
        body_preview = r.text[:400]
        log(f'  [{status}] {label}')
        log(f'        len={len(r.text)}  body={body_preview}')
    except Exception as e:
        log(f'  [ERR] {label}: {str(e)[:120]}')
    log()

# ══════════════════════════════════════════════════════
log('='*60)
log('A. Ambil daftar kode valid dari /wla/v1/app')
log('='*60)

valid_codes = []
r_app = get(f'{BASE}/wp-json/wla/v1/app')
if r_app and r_app.status_code == 200:
    log(f'  [200] /wla/v1/app  len={len(r_app.text)}')
    log(f'  Preview: {r_app.text[:2000]}')
    try:
        data_app = r_app.json()
        # Cari field yang berisi list pasaran/market
        def find_codes(obj, depth=0):
            if depth > 5:
                return
            if isinstance(obj, dict):
                for k, v in obj.items():
                    if any(x in k.lower() for x in
                           ['code','pasaran','market','togel','slug','list']):
                        log(f'    Key "{k}": {str(v)[:300]}')
                    find_codes(v, depth+1)
            elif isinstance(obj, list):
                for item in obj:
                    find_codes(item, depth+1)
        find_codes(data_app)

        # Coba ekstrak semua string pendek (1-20 char) yang mungkin kode
        raw = r_app.text
        short_strings = re.findall(r'"([a-z0-9_-]{2,20})"', raw)
        freq = {}
        for s in short_strings:
            freq[s] = freq.get(s, 0) + 1
        # Kandidat kode: string yang muncul ≥ 2x, bukan kata WP/JSON biasa
        ignore = {'true','false','null','get','post','id','name','type',
                  'code','data','list','status','error','message','slug',
                  'routes','methods','endpoints','namespace','context',
                  'required','default','args','description','items'}
        candidates = [s for s,c in sorted(freq.items(), key=lambda x:-x[1])
                      if s not in ignore and c >= 2]
        log(f'\n  Kandidat kode dari /app: {candidates[:30]}')
        valid_codes = candidates[:30]
    except Exception as e:
        log(f'  Parse error: {e}')
else:
    code = r_app.status_code if r_app else 'N/A'
    log(f'  [{code}] /wla/v1/app  body={r_app.text[:200] if r_app else "no response"}')

# ══════════════════════════════════════════════════════
log('\n' + '='*60)
log('B. Scrape JS plugin untuk cari kode valid')
log('='*60)

js_codes = []
js_url = f'{BASE}/wp-content/plugins/wla-premium-hub/app/framework/js/premium-hub.js'
r_js = get(js_url)
if r_js and r_js.status_code == 200:
    js = r_js.text
    log(f'  JS len={len(js):,}')

    # Cari array/object berisi kode pasaran
    # Pola: ["hk","sgp",...] atau {code:"xxx"}
    arr_matches = re.findall(r'\[(["\'][a-z0-9_-]+["\'](?:\s*,\s*["\'][a-z0-9_-]+["\']){2,})\]', js)
    for m in arr_matches[:5]:
        log(f'  Array ditemukan: [{m[:200]}]')
        codes_in_arr = re.findall(r'["\']([a-z0-9_-]+)["\']', m)
        js_codes.extend(codes_in_arr)

    # Pola: code: "xxx" atau "code":"xxx"
    inline_codes = re.findall(r'["\']?code["\']?\s*[:=]\s*["\']([a-z0-9_-]+)["\']', js, re.I)
    log(f'  inline code= values: {list(set(inline_codes))[:20]}')
    js_codes.extend(inline_codes)

    # Cari nama pasaran spesifik
    known_pattern = re.findall(
        r'["\']([a-z]{2,12}(?:pool|prize|lotto|4d|togel)?[a-z0-9]*)["\']', js)
    freq2 = {}
    for s in known_pattern:
        freq2[s] = freq2.get(s, 0) + 1
    top_js = [s for s,c in sorted(freq2.items(), key=lambda x:-x[1]) if c >= 3]
    log(f'  Top strings (freq≥3): {top_js[:30]}')
    js_codes.extend(top_js[:20])

    # Dump 500 char sekitar kata "code" pertama
    idx = js.find('"code"')
    if idx > -1:
        log(f'\n  Context sekitar "code": {js[max(0,idx-50):idx+300]}')
else:
    log(f'  [{r_js.status_code if r_js else "ERR"}] JS tidak dapat diakses')

# ══════════════════════════════════════════════════════
log('\n' + '='*60)
log('C. Scrape halaman paito untuk cari kode dari URL/HTML')
log('='*60)

page_codes = []
pages_to_check = [
    BASE + '/',
    BASE + '/paito-hk/',
    BASE + '/paito-sgp/',
    BASE + '/paito-sdy/',
]
for pg in pages_to_check:
    r_pg = get(pg, accept_html=True)
    if r_pg and r_pg.status_code == 200:
        html = r_pg.text
        # Cari data-code, data-market, data-pasaran
        attrs = re.findall(r'data-(?:code|market|pasaran|slug)=["\']([^"\']+)["\']', html)
        log(f'  {pg} → data-* attrs: {list(set(attrs))[:15]}')
        page_codes.extend(attrs)

        # Cari dari wp-json inline
        json_inline = re.findall(r'["\']code["\']:\s*["\']([^"\']+)["\']', html)
        if json_inline:
            log(f'    JSON inline code: {json_inline[:10]}')
            page_codes.extend(json_inline)

# ══════════════════════════════════════════════════════
log('\n' + '='*60)
log('D. Coba semua kode kandidat ke bot-trek')
log('='*60)

URL_TREK  = f'{BASE}/wp-json/wla/v1/bot-trek'
URL_BATCH = f'{BASE}/wp-json/wla/v1/bot-trek-batch'

# Gabung semua kandidat, deduplikasi
all_candidates = list(dict.fromkeys(valid_codes + js_codes + page_codes))
# Tambah tebakan manual berdasarkan pola togel Indonesia
manual_guesses = [
    # format dengan underscore/dash
    'hong_kong','hong-kong','hongkong_pools','hk_pools','hk-pools',
    'hongkongpools','hkpools',
    # format numerik
    'hk4d','sgp4d','sdy4d',
    # format dengan suffix
    'hk_malam','hk_siang','hks','hkm',
    # kemungkinan ID numerik
    '1','2','3','4','5',
    # nama lengkap
    'hongkong','singapore','sydney','macau','taiwan',
    'toto_hk','toto_sgp',
    # format dari fetch_all.py sebelumnya (kode internal app)
    'HKG','SGP','SDY','MAC','TWN',
]
all_candidates = list(dict.fromkeys(all_candidates + manual_guesses))
log(f'Total kandidat: {len(all_candidates)} → {all_candidates}')
log()

found_valid = []
for code_val in all_candidates:
    time.sleep(0.3)
    try:
        r = requests.get(URL_TREK, headers=HEADERS,
                         params={'code': code_val},
                         timeout=8, verify=False)
        body = r.text[:200]
        log(f'  [{r.status_code}] code={code_val:<20} body={body}')
        # Kalau bukan error kode tidak valid, tandai
        if 'tidak valid' not in body and 'invalid' not in body.lower():
            found_valid.append(code_val)
            log(f'  *** VALID CODE FOUND: {code_val} ***')
    except Exception as e:
        log(f'  [ERR] code={code_val}: {e}')

# ══════════════════════════════════════════════════════
log('\n' + '='*60)
log('E. bot-trek-batch dengan format codes[] (PHP array)')
log('='*60)

# Format PHP array: ?codes[]=hk&codes[]=sgp
# requests tidak langsung support ini, pakai manual URL encode

import urllib.parse

def probe_batch_array(label, code_list, extra_params=None):
    """Kirim codes[] dalam PHP array format"""
    time.sleep(0.35)
    parts = [f'codes[]={urllib.parse.quote(c)}' for c in code_list]
    if extra_params:
        for k, v in extra_params.items():
            parts.append(f'{k}={v}')
    qs = '&'.join(parts)
    full_url = f'{URL_BATCH}?{qs}'
    try:
        r = requests.get(full_url, headers=HEADERS, timeout=10, verify=False)
        log(f'  [{r.status_code}] {label}')
        log(f'        URL={full_url[:100]}')
        log(f'        len={len(r.text)}  body={r.text[:400]}')
    except Exception as e:
        log(f'  [ERR] {label}: {e}')
    log()

probe_batch_array('codes[]=[hk]', ['hk'])
probe_batch_array('codes[]=[hk,sgp,sdy]', ['hk','sgp','sdy'])
probe_batch_array('codes[]=[hongkong]', ['hongkong'])
probe_batch_array('codes[]=[HKG,SGP,SDY]', ['HKG','SGP','SDY'])

# Kalau ada kode valid dari section D, coba juga
if found_valid:
    log(f'\n  Kode valid ditemukan: {found_valid}')
    probe_batch_array(f'codes[]={found_valid}', found_valid)
    probe_batch_array(f'codes[]={found_valid} + limit=100',
                      found_valid, {'limit': 100})

# POST dengan JSON array
log('\n--- POST bot-trek-batch JSON ---')
json_bodies = [
    {'codes': ['hk']},
    {'codes': ['hk','sgp','sdy']},
    {'codes': ['HKG','SGP','SDY']},
]
if found_valid:
    json_bodies.append({'codes': found_valid})

for b in json_bodies:
    probe(f'POST {b}', URL_BATCH, method='POST', body=b)

# Simpan
with open('debug_api_v5.txt', 'w', encoding='utf-8') as f:
    f.write('\n'.join(out))
print('\n→ Saved to debug_api_v5.txt')
