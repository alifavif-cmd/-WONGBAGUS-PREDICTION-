"""
fetch_all.py — WongBagus Scraper v5
Satu halaman /data-pengeluaran-togel/ untuk semua pasaran.
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

# ─────────────────────────────────────────────────────────────
# Halaman utama listing semua pasaran
# ─────────────────────────────────────────────────────────────
LISTING_URLS = [
    "https://www.angkanet.com/data-pengeluaran-togel/",
    "https://angkanet.com/data-pengeluaran-togel/",
    "https://159.65.133.131/data-pengeluaran-togel/",
]

# ─────────────────────────────────────────────────────────────
# Mapping: keyword di halaman → kode pasaran kita
# Urutan keyword dari yang paling spesifik ke umum
# ─────────────────────────────────────────────────────────────
KEYWORD_MAP = [
    # (keyword_lowercase, kode)
    ("hongkong lotto",   "hkl"),
    ("hk lotto",         "hkl"),
    ("hklotto",          "hkl"),
    ("hong kong lotto",  "hkl"),
    ("hongkong pools",   "hk"),
    ("hongkong",         "hk"),
    ("singapore pools",  "sgp"),
    ("singapore",        "sgp"),
    ("sydney lotto",     "sdl"),
    ("sdlotto",          "sdl"),
    ("sydney pools",     "sdy"),
    ("sydney",           "sdy"),
    ("magnum cambodia",  "kam"),
    ("cambodia",         "kam"),
    ("kamboja",          "kam"),
    ("bullseye",         "bull"),
    ("china pools",      "chn"),
    ("chinapools",       "chn"),
    ("china",            "chn"),
    ("japan",            "jpn"),
    ("jepang",           "jpn"),
    ("taiwan",           "twn"),
]

# Info display per pasaran
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


# ─────────────────────────────────────────────────────────────
# HELPER
# ─────────────────────────────────────────────────────────────

def is_valid_togel(s: str) -> bool:
    """True jika string adalah angka 4 digit bukan tahun."""
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


def keyword_to_kode(text: str) -> str | None:
    """Cocokkan teks ke kode pasaran berdasarkan KEYWORD_MAP."""
    low = text.lower()
    for kw, kode in KEYWORD_MAP:
        if kw in low:
            return kode
    return None


# ─────────────────────────────────────────────────────────────
# SCRAPER UTAMA — satu halaman listing
# ─────────────────────────────────────────────────────────────

def scrape_listing() -> dict:
    """
    Fetch halaman /data-pengeluaran-togel/ dan ekstrak semua result.
    Return dict: {kode: result_str}
    """
    for url in LISTING_URLS:
        try:
            print(f"  [FETCH] {url}")
            resp = requests.get(url, headers=HEADERS, timeout=15,
                                verify=False, allow_redirects=True)
            print(f"  [HTTP] {resp.status_code} | {len(resp.text)} chars")

            if resp.status_code != 200:
                continue

            soup = BeautifulSoup(resp.text, "html.parser")
            results = {}

            # ── STRATEGI 1: Cari baris tabel yang punya nama pasaran + angka 4 digit ──
            for row in soup.find_all("tr"):
                cells = row.find_all(["td", "th"])
                if len(cells) < 2:
                    continue

                row_text = row.get_text(separator=" ", strip=True)

                # Cari kode pasaran dari teks baris
                kode = keyword_to_kode(row_text)
                if not kode:
                    continue

                # Cari angka 4 digit valid dalam baris ini
                nums = re.findall(r"\b(\d{4})\b", row_text)
                valid = [n for n in nums if is_valid_togel(n)]

                if valid and kode not in results:
                    results[kode] = valid[0]   # ambil yang pertama (paling dekat nama pasaran)
                    print(f"  [ROW] {kode.upper()}: {valid[0]}")

            if results:
                print(f"\n  ✅ Berhasil dari {url} | {len(results)} pasaran ditemukan")
                return results

            # ── STRATEGI 2: Cari elemen list/card dengan nama + angka ──
            print(f"  [FALLBACK] Coba strategi elemen non-tabel...")
            for el in soup.find_all(["div", "li", "article", "section"]):
                txt = el.get_text(separator=" ", strip=True)
                if len(txt) > 200 or len(txt) < 5:
                    continue

                kode = keyword_to_kode(txt)
                if not kode:
                    continue

                nums = re.findall(r"\b(\d{4})\b", txt)
                valid = [n for n in nums if is_valid_togel(n)]

                if valid and kode not in results:
                    results[kode] = valid[0]
                    print(f"  [EL] {kode.upper()}: {valid[0]}")

            if results:
                print(f"\n  ✅ Berhasil (fallback) dari {url} | {len(results)} pasaran")
                return results

            print(f"  [KOSONG] Tidak ada data di {url}")

        except Exception as e:
            print(f"  [ERR] {url}: {type(e).__name__}: {e}")

    print("  ❌ Semua URL listing gagal!")
    return {}


# ─────────────────────────────────────────────────────────────
# SCRAPER INDIVIDUAL — fallback per-pasaran jika listing gagal
# ─────────────────────────────────────────────────────────────

INDIVIDUAL_PATHS = {
    "hk":   "/data-pengeluaran-togel-hongkong-pools/",
    "hkl":  "/data-pengeluaran-togel-hklotto/",
    "sgp":  "/data-pengeluaran-togel-singapore/",
    "sdy":  "/data-pengeluaran-togel-sydney-pools/",
    "sdl":  "/data-pengeluaran-togel-sdlotto/",
    "kam":  "/data-pengeluaran-togel-magnum-cambodia/",
    "bull": "/data-pengeluaran-togel-bullseye/",
    "chn":  "/data-pengeluaran-togel-chinapools/",
    "jpn":  "/data-pengeluaran-togel-japan/",
    "twn":  "/data-pengeluaran-togel-taiwan/",
}

INDIVIDUAL_DOMAINS = [
    "https://www.angkanet.com",
    "https://angkanet.com",
    "https://159.65.133.131",
]

def scrape_individual(kode: str) -> str | None:
    path = INDIVIDUAL_PATHS.get(kode, "")
    for domain in INDIVIDUAL_DOMAINS:
        try:
            resp = requests.get(domain + path, headers=HEADERS,
                                timeout=12, verify=False, allow_redirects=True)
            if resp.status_code != 200:
                continue
            soup = BeautifulSoup(resp.text, "html.parser")
            # <td> persis 4 digit
            for td in soup.find_all("td"):
                t = td.get_text(strip=True)
                if re.match(r"^\d{4}$", t) and is_valid_togel(t):
                    return t
            # fallback scan teks
            nums = re.findall(r"\b(\d{4})\b", soup.get_text())
            valid = [n for n in nums if is_valid_togel(n)]
            if valid:
                return valid[-1]
        except Exception:
            pass
    return None


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

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
    print(f"  WongBagus Scraper v5 | {now.strftime('%d/%m/%Y %H:%M')}")
    print(f"{'='*55}\n")

    # ── Tahap 1: Scrape halaman listing (satu request untuk semua) ──
    print("📡 Scraping halaman listing...")
    scraped = scrape_listing()
    print()

    # ── Tahap 2: Per-pasaran fallback untuk yang belum dapat ──
    missing = [k for k in PASARAN_INFO if k not in scraped]
    if missing:
        print(f"🔍 Fallback per-pasaran untuk: {', '.join(k.upper() for k in missing)}")
        for kode in missing:
            r = scrape_individual(kode)
            if r:
                scraped[kode] = r
                print(f"  [IND] {kode.upper()}: {r}")
            else:
                print(f"  [IND] {kode.upper()}: gagal")
        print()

    # ── Tahap 3: Update current_data ──
    print("📝 Update result.json...")
    for kode, (nama, jam_tutup) in PASARAN_INFO.items():
        result   = scraped.get(kode)
        old_val  = current_data.get(kode, {}).get("result", "")
        sudah    = is_already_out(jam_tutup)

        if result and is_valid_togel(result):
            status = "sudah" if sudah else "belum"
            current_data[kode] = {
                "result":  result,
                "tgl":     tgl_str,
                "status":  status,
                "updated": time_str,
                "name":    nama,
                "jam":     jam_tutup,
            }
            icon = "✅" if status == "sudah" else "⏳"
            print(f"  {icon} [{kode.upper()}] {result}")
        elif old_val and not is_stale_year(old_val):
            print(f"  ⚠️  [{kode.upper()}] Gagal, pertahankan lama: {old_val}")
        else:
            current_data[kode] = {
                "result":  "????",
                "tgl":     tgl_str,
                "status":  "belum",
                "updated": time_str,
                "name":    nama,
                "jam":     jam_tutup,
            }
            print(f"  ❌ [{kode.upper()}] Gagal → ????")

    current_data["_meta"] = {
        "updated": now.strftime("%Y-%m-%d %H:%M WIB"),
        "date":    tgl_str,
        "source":  "angkanet-listing-v5",
        "total":   len(PASARAN_INFO),
    }

    with open("result.json", "w") as f:
        json.dump(current_data, f, indent=2, ensure_ascii=False)

    ok = sum(1 for k in PASARAN_INFO
             if is_valid_togel(current_data.get(k, {}).get("result", "")))
    print(f"\n💾 Selesai | ✅ {ok}/{len(PASARAN_INFO)} pasaran berhasil")


if __name__ == "__main__":
    update_json()
