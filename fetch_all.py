"""
fetch_all.py — WongBagus Prediction Auto Scraper v4
Strategi: coba 3 domain Angkanet + fallback API, debug lengkap, tidak simpan data ngawur.
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
# KONFIGURASI SUMBER
# ─────────────────────────────────────────────────────────────

# Semua domain Angkanet dicoba berurutan
ANGKANET_DOMAINS = [
    "https://www.angkanet.com",
    "https://angkanet.com",
    "https://159.65.133.131",
]

ANGKANET_PATHS = {
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

# Pasaran yang hasil resminya sama dengan pasaran lain (mirror)
# Jika scrape gagal, ambil dari sumber mirrornya
MIRROR_MAP = {
    "hkl": "hk",   # HK Lotto = Hongkong Pools
    "sdl": "sdy",  # Sydney Lotto = Sydney Pools
}

# Beberapa path alternatif untuk pasaran yang sering gagal
ANGKANET_ALT_PATHS = {
    "hkl": ["/data-pengeluaran-togel-hk-lotto/",
             "/data-pengeluaran-togel-hongkonglotto/"],
    "sdl": ["/data-pengeluaran-togel-sydney-lotto/",
             "/data-pengeluaran-togel-sdlotto-pools/"],
    "jpn": ["/data-pengeluaran-togel-jepang/",
             "/data-pengeluaran-togel-japan-pools/"],
}

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

def is_valid_togel(token: str) -> bool:
    """True jika token bisa jadi result togel (bukan tahun/noise)."""
    if not token or token.lower() == "xxxx":
        return False
    try:
        n = int(token)
        return not (1800 <= n <= 2199)   # exclude angka tahun
    except ValueError:
        return False


def is_stale_year(val) -> bool:
    """True jika value terlihat seperti tahun (1800-2199)."""
    try:
        return 1800 <= int(str(val)) <= 2199
    except (ValueError, TypeError):
        return False


def extract_results_from_html(html: str) -> list:
    """
    Parse HTML, kembalikan list token 4-digit valid (bukan tahun).
    Coba <td> dulu, lalu CSS class result, lalu scan teks.
    """
    soup = BeautifulSoup(html, "html.parser")
    found = []

    # Prioritas 1: <td> yang isinya persis 4 digit valid
    for td in soup.find_all("td"):
        raw = td.get_text(strip=True)
        if re.match(r"^\d{4}$", raw) and is_valid_togel(raw):
            found.append(raw)

    if found:
        return found

    # Prioritas 2: elemen dengan class/id terkait result
    for el in soup.find_all(
        class_=re.compile(r"result|angka|keluaran|pengeluaran|nomor|number", re.I)
    ):
        for m in re.finditer(r"\b(\d{4})\b", el.get_text()):
            if is_valid_togel(m.group(1)):
                found.append(m.group(1))

    if found:
        return found

    # Prioritas 3: scan semua teks (xxxx boleh masuk)
    for m in re.finditer(r"\b(\d{4}|xxxx)\b", soup.get_text(), re.I):
        t = m.group(1)
        if t.lower() == "xxxx" or is_valid_togel(t):
            found.append(t)

    return found


# ─────────────────────────────────────────────────────────────
# SCRAPER
# ─────────────────────────────────────────────────────────────

def scrape_angkanet(kode: str) -> tuple:
    """Coba semua domain + path alternatif. Return (result, is_pending) atau (None, False)."""
    # Kumpulkan semua path yang akan dicoba
    paths_to_try = []
    if kode in ANGKANET_PATHS:
        paths_to_try.append(ANGKANET_PATHS[kode])
    if kode in ANGKANET_ALT_PATHS:
        paths_to_try.extend(ANGKANET_ALT_PATHS[kode])

    if not paths_to_try:
        return None, False

    for path in paths_to_try:
        for domain in ANGKANET_DOMAINS:
            url = domain + path
            try:
                resp = requests.get(url, headers=HEADERS, timeout=12,
                                    verify=False, allow_redirects=True)
                print(f"    [TRY] {domain}{path} → HTTP {resp.status_code} | {len(resp.text)} chars")

                if resp.status_code != 200:
                    continue

                tokens = extract_results_from_html(resp.text)
                print(f"    [TOKENS] last 8: {tokens[-8:] if tokens else '[]'}")

                if not tokens:
                    continue

                is_pending = tokens[-1].lower() == "xxxx"
                valid = [t for t in tokens if t.lower() != "xxxx"]

                if valid:
                    print(f"    [HIT] result={valid[-1]} | pending={is_pending}")
                    return valid[-1], is_pending

            except Exception as e:
                print(f"    [ERR] {domain}: {type(e).__name__}: {e}")

    return None, False


# ─────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────

def is_already_out(jam_str: str) -> bool:
    now = datetime.datetime.now()
    h, m = map(int, jam_str.split(":"))
    return now >= now.replace(hour=h, minute=m, second=0, microsecond=0)


def update_json():
    # Load data lama
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
    print(f"  SCRAPE {len(PASARAN_INFO)} PASARAN | {now.strftime('%d/%m/%Y %H:%M')}")
    print(f"{'='*55}\n")

    for kode, (nama, jam_tutup) in PASARAN_INFO.items():
        print(f"▶ [{kode.upper()}] {nama} — tutup {jam_tutup} WIB")

        result, is_pending = scrape_angkanet(kode)

        old_entry = current_data.get(kode, {})
        old_val   = old_entry.get("result", "")

        if result:
            sudah = is_already_out(jam_tutup)
            status = "belum" if (is_pending or not sudah) else "sudah"
            current_data[kode] = {
                "result":  result,
                "tgl":     tgl_str,
                "status":  status,
                "updated": time_str,
                "name":    nama,
                "jam":     jam_tutup,
            }
            icon = "⏳" if status == "belum" else "✅"
            print(f"  {icon} RESULT: {result}\n")

        else:
            # Coba mirror pasaran (HKL→HK, SDL→SDY)
            mirror_kode = MIRROR_MAP.get(kode)
            mirror_result = None
            if mirror_kode and current_data.get(mirror_kode, {}).get("result"):
                mirror_val = current_data[mirror_kode]["result"]
                if not is_stale_year(mirror_val) and mirror_val != "????":
                    mirror_result = mirror_val
                    print(f"  🔁 Mirror dari [{mirror_kode.upper()}]: {mirror_result}")

            if mirror_result:
                sudah = is_already_out(jam_tutup)
                status = "belum" if not sudah else "sudah"
                current_data[kode] = {
                    "result":  mirror_result,
                    "tgl":     tgl_str,
                    "status":  status,
                    "updated": time_str,
                    "name":    nama,
                    "jam":     jam_tutup,
                    "mirror":  mirror_kode,
                }
                print(f"  ✅ RESULT (mirror): {mirror_result}\n")

            elif old_val and not is_stale_year(old_val):
                print(f"  ⚠️  Gagal — pertahankan lama: {old_val}\n")
            else:
                current_data[kode] = {
                    "result":  "????",
                    "tgl":     tgl_str,
                    "status":  "belum",
                    "updated": time_str,
                    "name":    nama,
                    "jam":     jam_tutup,
                }
                print(f"  ❌ Gagal + lama ngawur ({old_val}) → set '????'\n")

    current_data["_meta"] = {
        "updated": now.strftime("%Y-%m-%d %H:%M WIB"),
        "date":    tgl_str,
        "source":  "wongbagus-scraper-v4",
        "total":   len(PASARAN_INFO),
    }

    with open("result.json", "w") as f:
        json.dump(current_data, f, indent=2, ensure_ascii=False)

    total = len(PASARAN_INFO)
    ok    = sum(1 for k in PASARAN_INFO if current_data.get(k, {}).get("result", "????") not in ("????",))
    print(f"💾 result.json disimpan | ✅ {ok}/{total} pasaran berhasil")
    print("📤 Push via git Actions step.\n")


if __name__ == "__main__":
    update_json()
