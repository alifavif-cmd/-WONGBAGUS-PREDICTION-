#!/usr/bin/env python3
"""
fetch_hk.py
Scrape hasil HK dari angkanet (paito-harian-hongkong-pools)
dan simpan/update hk.json — dijalankan via GitHub Actions.

Source: https://159.65.133.131/paito-harian-hongkong-pools/
"""

import requests
import json
import re
import os
import sys
from datetime import datetime, timezone, timedelta
from bs4 import BeautifulSoup
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ── Konfigurasi ─────────────────────────────────────────────────────
URL_PAITO  = 'https://159.65.133.131/paito-harian-hongkong-pools/'
OUTPUT     = 'hk.json'
MAX_ROWS   = 365   # minta 1 tahun data ke angkanet

HEADERS = {
    'User-Agent': (
        'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
        'AppleWebKit/537.36 (KHTML, like Gecko) '
        'Chrome/124.0.0.0 Safari/537.36'
    ),
    'Referer':         'https://159.65.133.131/',
    'Accept-Language': 'id-ID,id;q=0.9,en;q=0.8',
    'Accept':          'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
}

# Senin=0 … Minggu=6 → label Indonesia
DAY_LABEL = {0:'SEN', 1:'SEL', 2:'RAB', 3:'KAM', 4:'JUM', 5:'SAB', 6:'MIN'}


# ── Waktu WIB ────────────────────────────────────────────────────────
def now_wib_str():
    wib = timezone(timedelta(hours=7))
    return datetime.now(wib).strftime('%Y-%m-%d %H:%M WIB')


# ── Fetch HTML ────────────────────────────────────────────────────────
def fetch_html(rows=MAX_ROWS):
    """
    Ambil HTML dari angkanet paito-harian.
    Parameter ?rows=N meminta jumlah baris data.
    """
    params = {'rows': rows}
    resp = requests.get(
        URL_PAITO, params=params,
        headers=HEADERS, verify=False, timeout=25
    )
    resp.raise_for_status()
    return resp.text


# ── Parse HTML ────────────────────────────────────────────────────────
def parse_html(html):
    """
    Parse tabel paito-harian angkanet.
    Struktur tabel:
      kolom 0 : tanggal (DD-MM-YYYY)
      kolom 1 : digit AS
      kolom 2 : digit KOP
      kolom 3 : digit KEP
      kolom 4 : digit EK
      kolom 5+ : jumlah & taysen (diabaikan)
    Baris terakhir bertanda 'x' = belum keluar, dilewati.
    """
    soup = BeautifulSoup(html, 'html.parser')
    results = []

    for table in soup.find_all('table'):
        rows = table.find_all('tr')
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) < 5:
                continue

            date_text = cells[0].get_text(strip=True)

            # Cocokkan format DD-MM-YYYY
            m = re.match(r'^(\d{2})-(\d{2})-(\d{4})$', date_text)
            if not m:
                continue

            dd, mm, yyyy = m.groups()
            date_iso = f'{yyyy}-{mm}-{dd}'

            # Ambil 4 digit hasil (kolom 1–4)
            digits = []
            for cell in cells[1:5]:
                t = cell.get_text(strip=True)
                if re.match(r'^\d$', t):
                    digits.append(t)

            if len(digits) != 4:
                continue

            result = ''.join(digits)

            # Hitung nama hari
            try:
                dt = datetime.strptime(date_iso, '%Y-%m-%d')
                day_name = DAY_LABEL[dt.weekday()]
            except Exception:
                day_name = ''

            results.append({
                'date':   date_iso,
                'result': result,
                'day':    day_name,
            })

    return results


# ── Load existing hk.json ─────────────────────────────────────────────
def load_existing():
    if os.path.exists(OUTPUT):
        try:
            with open(OUTPUT, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f'  [WARN] Gagal baca {OUTPUT}: {e}')
    return {'results': []}


# ── Merge new + existing ──────────────────────────────────────────────
def merge(existing_data, new_results):
    """
    Merge: update result yang salah, tambah yang baru, urutkan terbaru di atas.
    """
    ex_map = {r['date']: r for r in existing_data.get('results', [])}

    added   = 0
    updated = 0

    for r in new_results:
        if r['date'] in ex_map:
            old_result = ex_map[r['date']].get('result')
            if old_result != r['result']:
                ex_map[r['date']]['result'] = r['result']
                ex_map[r['date']]['day']    = r.get('day', ex_map[r['date']].get('day', ''))
                updated += 1
        else:
            ex_map[r['date']] = r
            added += 1

    merged = sorted(ex_map.values(), key=lambda x: x['date'], reverse=True)
    return merged, added, updated


# ── Save ──────────────────────────────────────────────────────────────
def save(merged_results):
    output = {
        'lastUpdate':   now_wib_str(),
        'totalResult':  len(merged_results),
        'source':       URL_PAITO,
        'results':      merged_results,
    }
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, separators=(',', ':'))


# ── Main ──────────────────────────────────────────────────────────────
def main():
    ts = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f'[{ts}] Mulai fetch HK dari angkanet...')
    print(f'  URL : {URL_PAITO}?rows={MAX_ROWS}')

    # 1. Fetch
    try:
        html = fetch_html()
        print(f'  HTML : {len(html):,} karakter')
    except Exception as e:
        print(f'  ERROR fetch: {e}')
        sys.exit(1)

    # 2. Parse
    new_results = parse_html(html)
    print(f'  Parse: {len(new_results)} baris ditemukan')

    if not new_results:
        print('  ERROR: Tidak ada data berhasil di-parse!')
        print('         Kemungkinan struktur HTML berubah atau data di-load via AJAX.')
        print('         Cek manual: ' + URL_PAITO)
        sys.exit(1)

    # 3. Merge dengan existing
    existing_data = load_existing()
    merged, added, updated = merge(existing_data, new_results)

    print(f'  Merge: +{added} baru, ~{updated} diupdate, total {len(merged)} result')

    if merged:
        terbaru = merged[0]
        print(f'  Terbaru: {terbaru["date"]} ({terbaru.get("day","")}) = {terbaru["result"]}')

    # 4. Simpan
    save(merged)
    print(f'  Saved: {OUTPUT} ✓')
    print(f'  lastUpdate: {now_wib_str()}')


if __name__ == '__main__':
    main()
