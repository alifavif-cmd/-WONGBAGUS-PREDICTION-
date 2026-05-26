"""
PATCH FIX — History Accumulation untuk fetch_all.py
====================================================
Masalah: result.json lama tidak punya field 'history' per pasaran
         → BACKFILL selalu skip → history selalu 1 entry

Solusi: Fungsi-fungsi ini menggantikan / ditambahkan ke fetch_all.py
        di bagian load data lama + save result.

CARA PAKAI:
  Cari bagian "Data lama" dan bagian SAVE di fetch_all.py,
  ganti/tambahkan dengan logika di bawah ini.
"""

import json, os
from datetime import datetime, timezone, timedelta

RESULT_FILE  = 'result.json'
HISTORY_MAX  = 30          # simpan 30 hari
TZ_WIB       = timezone(timedelta(hours=7))


# ─────────────────────────────────────────────────────────
# 1. LOAD DATA LAMA + MIGRATE HISTORY
# ─────────────────────────────────────────────────────────
def load_old_data(path=RESULT_FILE):
    """
    Load result.json lama.
    Return dict: { kode: { 'result': '...', 'tgl': '...', 'history': [...] } }
    'history' adalah list [{'tgl': ..., 'result': ...}, ...]  terbaru di depan.
    """
    if not os.path.exists(path):
        print(f'  [LOAD] {path} tidak ada — fresh start')
        return {}

    try:
        with open(path, encoding='utf-8') as f:
            raw = json.load(f)
    except Exception as e:
        print(f'  [LOAD] Error baca {path}: {e}')
        return {}

    # raw bisa list atau dict
    if isinstance(raw, list):
        items = raw
    elif isinstance(raw, dict):
        items = list(raw.values()) if raw else []
    else:
        items = []

    old = {}
    migrated = 0
    for item in items:
        if not isinstance(item, dict):
            continue
        kode = item.get('kode') or item.get('code') or item.get('pasaran')
        if not kode:
            continue
        kode = kode.lower()

        history = item.get('history', [])

        # MIGRATE: jika history kosong tapi ada result, buat 1 entry dari data lama
        if not history:
            res  = item.get('result') or item.get('angka') or item.get('keluaran')
            tgl  = item.get('tgl') or item.get('date') or item.get('tanggal', '')
            if res and tgl:
                history = [{'tgl': tgl, 'result': str(res)}]
                migrated += 1

        old[kode] = {
            'result'  : item.get('result') or item.get('angka', ''),
            'tgl'     : item.get('tgl') or item.get('date', ''),
            'nama'    : item.get('nama') or item.get('name', kode),
            'history' : history,
        }

    print(f'  [LOAD] {len(old)} pasaran lama | migrated history: {migrated}')
    return old


# ─────────────────────────────────────────────────────────
# 2. MERGE hasil fetch baru ke old_data (akumulasi history)
# ─────────────────────────────────────────────────────────
def merge_new_result(old_data: dict, kode: str, result_baru: str,
                     tgl_baru: str, nama: str = '') -> dict:
    """
    Ambil entry lama (jika ada), tambahkan entry baru ke history.
    Return dict entry yang siap disimpan.
    """
    kode = kode.lower()
    old  = old_data.get(kode, {})
    history = list(old.get('history', []))  # copy

    # Tambahkan entry hari ini di depan (jika beda hari / belum ada)
    entry_baru = {'tgl': tgl_baru, 'result': str(result_baru)}
    if not history or history[0].get('tgl') != tgl_baru:
        history.insert(0, entry_baru)

    # Trim ke HISTORY_MAX
    history = history[:HISTORY_MAX]

    return {
        'kode'    : kode,
        'nama'    : nama or old.get('nama', kode),
        'result'  : str(result_baru),
        'tgl'     : tgl_baru,
        'history' : history,
        '_hist_n' : len(history),
    }


# ─────────────────────────────────────────────────────────
# 3. SAVE result.json
# ─────────────────────────────────────────────────────────
def save_result(entries: list, path=RESULT_FILE):
    """
    Simpan list entries ke result.json.
    entries = [dict dari merge_new_result(), ...]
    """
    # Simpan sebagai list (kompatibel dengan fetch_all lama)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(entries, f, ensure_ascii=False, separators=(',', ':'))

    hist_counts = [e.get('_hist_n', 0) for e in entries]
    rata = sum(hist_counts) / len(hist_counts) if hist_counts else 0
    print(f'  [SAVE] {path} → {len(entries)} pasaran | '
          f'hist rata={rata:.1f} | max={max(hist_counts, default=0)}')


# ─────────────────────────────────────────────────────────
# CONTOH INTEGRASI di fetch_all.py
# ─────────────────────────────────────────────────────────
"""
Ganti bagian ini di fetch_all.py:

# ── LAMA (yang bikin history tidak akumulasi) ──
old_data = load_json(RESULT_FILE) or {}   # mungkin tidak load history

# ── BARU ──
from patch_history_fix import load_old_data, merge_new_result, save_result
old_data = load_old_data(RESULT_FILE)

# ... setelah fetch selesai, untuk setiap pasaran:
tgl_hari_ini = datetime.now(TZ_WIB).strftime('%Y-%m-%d')
entries_final = []
for kode, fetch_result in hasil_fetch.items():
    entry = merge_new_result(
        old_data    = old_data,
        kode        = kode,
        result_baru = fetch_result['result'],
        tgl_baru    = tgl_hari_ini,
        nama        = fetch_result.get('nama', kode),
    )
    entries_final.append(entry)

save_result(entries_final, RESULT_FILE)
"""

# ─────────────────────────────────────────────────────────
# TEST — jalankan langsung untuk cek logic
# ─────────────────────────────────────────────────────────
if __name__ == '__main__':
    # Simulasi result.json LAMA (format tanpa history)
    SAMPLE_OLD = [
        {'kode': 'hk',  'nama': 'Hongkong Pools', 'result': '4509', 'tgl': '2026-05-25'},
        {'kode': 'sgp', 'nama': 'Singapore',       'result': '2924', 'tgl': '2026-05-25'},
        {'kode': 'sdy', 'nama': 'Sydney Pools',    'result': '4266', 'tgl': '2026-05-25'},
    ]
    with open('_test_old.json', 'w') as f:
        json.dump(SAMPLE_OLD, f)

    print('=== TEST LOAD ===')
    old = load_old_data('_test_old.json')
    for k, v in old.items():
        print(f'  {k}: hist={v["history"]}')

    print('\n=== TEST MERGE hari ini ===')
    entries = []
    fetch_hari_ini = {
        'hk':  {'result': '1234', 'nama': 'Hongkong Pools'},
        'sgp': {'result': '5678', 'nama': 'Singapore'},
        'sdy': {'result': '9012', 'nama': 'Sydney Pools'},
    }
    tgl = '2026-05-26'
    for kode, data in fetch_hari_ini.items():
        e = merge_new_result(old, kode, data['result'], tgl, data['nama'])
        entries.append(e)
        print(f'  {kode}: hist_n={e["_hist_n"]} | {e["history"]}')

    save_result(entries, '_test_new.json')
    print('\nFile _test_new.json:')
    with open('_test_new.json') as f:
        print(json.dumps(json.load(f), indent=2, ensure_ascii=False)[:800])

    os.remove('_test_old.json')
    os.remove('_test_new.json')
    print('\nOK — patch siap dipakai!')
