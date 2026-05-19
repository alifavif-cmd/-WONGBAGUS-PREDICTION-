"""
fetch_all_v2.py — WongBagus Scraper v6
Scrape dari paito-harian per pasaran (data HTML langsung, tidak butuh JS).
"""

import requests
from bs4 import BeautifulSoup
import json
import re
import datetime
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) "
                  "Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "id-ID,id;q=0.9,en;q=0.8",
}

DOMAINS = [
    "https://159.65.133.131",
    "https://www.angkanet.com",
    "https://angkanet.com",
]

# Paito-harian paths — data HTML langsung tersedia tanpa JS
PAITO_PATHS = {
    "hk":   "/paito-harian-hongkong-pools/",
    "hkl":  "/paito-harian-hklotto/",
    "sgp":  "/paito-harian-singapore/",
    "sdy":  "/paito-harian-sydney-pools/",
    "sdl":  "/paito-harian-sdlotto/",
    "kam":  "/paito-harian-magnum-cambodia/",
    "bull": "/paito-harian-bullseye/",
    "chn":  "/paito-harian-chinapools/",
    "jpn":  "/paito-harian-japan/",
    "twn":  "/paito-harian-taiwan/",
}

PASARAN_INFO = {
    "hk":   ("Hongkong",     "23:00"),
    "hkl":  ("HK Lotto",     "23:00"),
    "sgp":  ("Singapore",    "17:40"),
    "sdy":  ("Sydney Pools", "13:45"),
    "sdl":  ("Sydney Lotto", "13:45"),
    "kam":  ("Kamboja",      "11:50"),
    "bull": ("Bullseye NZ",  "13:10"),
    "chn":  ("China Pools",  "15:30"),
    "jpn":  ("Japan",        "17:20"),
    "twn":  ("Taiwan",       "20:45"),
}


def is_valid_togel(s: str) -> bool:
    if not s:
        return False
    try:
        n = int(s)
        return len(s) == 4 and not (1800 <= n <= 2199)
    except ValueError:
        return False


def is_stale_year(val) -> bool:
    try:
        return 1800 <= int(str(val)) <= 2199
    except (ValueError, TypeError):
        return False


def get_today_str() -> str:
    """Return today's date in format DD-MM-YYYY as shown in angkanet table."""
    return datetime.datetime.now().strftime("%d-%m-%Y")


def scrape_paito_harian(kode: str) -> str | None:
    """
    Scrape paito-harian page untuk pasaran tertentu.
    Cari baris dengan tanggal hari ini, ambil 4 digit pertama (result).
    """
    path = PAITO_PATHS.get(kode, "")
    today = get_today_str()

    for domain in DOMAINS:
        url = domain + path
        try:
            print(f"  [FETCH] {url}")
            resp = requests.get(url, headers=HEADERS, timeout=15,
                                verify=False, allow_redirects=True)
            print(f"  [HTTP] {resp.status_code} | {len(resp.text)} chars")

            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")

            # Cari tabel dengan kolom tanggal
            for table in soup.find_all("table"):
                rows = table.find_all("tr")
                for row in rows:
                    cells = row.find_all(["td", "th"])
                    if not cells:
                        continue

                    # Kolom pertama = tanggal
                    tgl_cell = cells[0].get_text(strip=True)

                    if today in tgl_cell:
                        # Kolom 2,3,4,5 = digit result (4 digit)
                        digits = []
                        for cell in cells[1:5]:
                            txt = cell.get_text(strip=True)
                            if re.match(r"^\d$", txt):
                                digits.append(txt)

                        if len(digits) == 4:
                            result = "".join(digits)
                            if is_valid_togel(result):
                                print(f"  [OK] {kode.upper()} {today}: {result}")
                                return result
                            else:
                                print(f"  [SKIP] {kode.upper()} result tidak valid: {result}")

            print(f"  [MISS] {kode.upper()}: tanggal {today} tidak ditemukan di {domain}")

        except Exception as e:
            print(f"  [ERR] {url}: {type(e).__name__}: {e}")

    return None


def is_already_out(jam_str: str) -> bool:
    now = datetime.datetime.now()
    h, m = map(int, jam_str.split(":"))
    return now >= now.replace(hour=h, minute=m, second=0, microsecond=0)


def update_json():
    try:
        with open("result.json", "r") as f:
            current_data = json.load(f)
        print("✅ result.json lama dimuat.\n")
    except Exception:
        current_data = {}
        print("⚠️  result.json tidak ada, mulai kosong.\n")

    now      = datetime.datetime.now()
    tgl_str  = now.strftime("%d/%m")
    time_str = now.strftime("%H:%M WIB")

    print(f"{'='*55}")
    print(f"  WongBagus Scraper v6 | {now.strftime('%d/%m/%Y %H:%M')}")
    print(f"  Sumber: paito-harian angkanet (HTML langsung)")
    print(f"{'='*55}\n")

    print("📝 Update result.json...\n")

    for kode, (nama, jam_tutup) in PASARAN_INFO.items():
        sudah = is_already_out(jam_tutup)
        old_val = current_data.get(kode, {}).get("result", "")

        if not sudah:
            print(f"  ⏳ [{kode.upper()}] Belum waktu ({jam_tutup} WIB), skip.")
            continue

        print(f"  🔍 Scraping {kode.upper()} ({nama})...")
        result = scrape_paito_harian(kode)
        print()

        if result and is_valid_togel(result):
            current_data[kode] = {
                "result":  result,
                "tgl":     tgl_str,
                "status":  "sudah",
                "updated": time_str,
                "name":    nama,
                "jam":     jam_tutup,
            }
            print(f"  ✅ [{kode.upper()}] {result}\n")
        elif old_val and not is_stale_year(old_val):
            print(f"  ⚠️  [{kode.upper()}] Gagal, pertahankan lama: {old_val}\n")
        else:
            current_data[kode] = {
                "result":  "????",
                "tgl":     tgl_str,
                "status":  "belum",
                "updated": time_str,
                "name":    nama,
                "jam":     jam_tutup,
            }
            print(f"  ❌ [{kode.upper()}] Gagal → ????\n")

    current_data["_meta"] = {
        "updated": now.strftime("%Y-%m-%d %H:%M WIB"),
        "date":    tgl_str,
        "source":  "angkanet-paito-harian-v6",
        "total":   len(PASARAN_INFO),
    }

    with open("result.json", "w") as f:
        json.dump(current_data, f, indent=2, ensure_ascii=False)

    ok = sum(1 for k in PASARAN_INFO
             if is_valid_togel(current_data.get(k, {}).get("result", "")))
    print(f"\n💾 Selesai | ✅ {ok}/{len(PASARAN_INFO)} pasaran berhasil")


if __name__ == "__main__":
    update_json()
