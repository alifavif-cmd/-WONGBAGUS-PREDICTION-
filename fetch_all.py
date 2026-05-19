import requests
from bs4 import BeautifulSoup
import json
import re
import datetime
import urllib3

# Nonaktifkan peringatan SSL karena pakai IP langsung
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

BASE_URL = "https://159.65.133.131"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

# Konfigurasi tiap pasaran: kode json -> (path angkanet, nama display, jam tutup WIB)
PASARAN_CONFIG = {
    "hk":   ("/data-pengeluaran-togel-hongkong-pools/", "Hongkong Pools",   "23:00"),
    "hkl":  ("/data-pengeluaran-togel-hklotto/",        "Hongkong Lotto",   "23:00"),
    "sgp":  ("/data-pengeluaran-togel-singapore/",      "Singapore Pools",  "17:40"),
    "sdy":  ("/data-pengeluaran-togel-sydney-pools/",   "Sydney Pools",     "13:45"),
    "sdl":  ("/data-pengeluaran-togel-sdlotto/",        "Sydney Lotto",     "13:45"),
    "kam":  ("/data-pengeluaran-togel-magnum-cambodia/","Kamboja",          "11:50"),
    "bull": ("/data-pengeluaran-togel-bullseye/",       "Bullseye NZ",      "13:10"),
    "chn":  ("/data-pengeluaran-togel-chinapools/",     "China Pools",      "15:30"),
    "jpn":  ("/data-pengeluaran-togel-japan/",          "Japan",            "17:20"),
    "twn":  ("/data-pengeluaran-togel-taiwan/",         "Taiwan",           "20:45"),
}


def scrape_pasaran(path):
    """
    Scrape halaman pasaran Angkanet dan ambil result terakhir yang valid (bukan xxxx).
    Return tuple: (result_4digit atau None, is_today_pending)
    """
    url = BASE_URL + path
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        if resp.status_code != 200:
            print(f"  [GAGAL] HTTP {resp.status_code} - {url}")
            return None, False

        soup = BeautifulSoup(resp.text, "html.parser")
        text = soup.get_text(separator=" ")

        # Ambil semua token yang berupa angka 4 digit atau 'xxxx'
        tokens = re.findall(r"\b(\d{4}|xxxx)\b", text, re.IGNORECASE)

        if not tokens:
            print(f"  [KOSONG] Tidak ada 4-digit ditemukan - {url}")
            return None, False

        # Cek apakah entry terakhir adalah xxxx (belum keluar hari ini)
        last_token = tokens[-1].lower()
        is_pending = (last_token == "xxxx")

        # Ambil result terakhir yang BUKAN xxxx
        valid_tokens = [t for t in tokens if t.lower() != "xxxx"]
        if not valid_tokens:
            return None, is_pending

        last_result = valid_tokens[-1]
        return last_result, is_pending

    except Exception as e:
        print(f"  [ERROR] {e} - {url}")
        return None, False


def is_already_out(jam_tutup_str):
    """Cek apakah sudah melewati jam tutup pasaran hari ini."""
    now = datetime.datetime.now()
    h, m = map(int, jam_tutup_str.split(":"))
    tutup = now.replace(hour=h, minute=m, second=0, microsecond=0)
    return now >= tutup


def update_json():
    # Load result.json existing (untuk preserve pasaran tambahan yang tidak di-scrape)
    try:
        with open("result.json", "r") as f:
            current_data = json.load(f)
        print("result.json loaded.")
    except Exception:
        current_data = {}
        print("result.json tidak ditemukan, mulai dari kosong.")

    now = datetime.datetime.now()
    tgl_str = now.strftime("%d/%m")
    time_str = now.strftime("%H:%M WIB")

    print(f"\n=== Mulai scrape {len(PASARAN_CONFIG)} pasaran | {now.strftime('%d/%m/%Y %H:%M WIB')} ===\n")

    for kode, (path, nama, jam_tutup) in PASARAN_CONFIG.items():
        print(f"Scraping [{kode.upper()}] {nama}...")
        result, is_pending = scrape_pasaran(path)

        sudah_waktunya = is_already_out(jam_tutup)

        if result:
            if is_pending or not sudah_waktunya:
                status = "belum"
            else:
                status = "sudah"

            current_data[kode] = {
                "result": result,
                "tgl": tgl_str,
                "status": status,
                "updated": time_str,
                "name": nama
            }
            flag = "⏳ BELUM" if status == "belum" else "✅ SUDAH"
            print(f"  {flag} | Result: {result} | Jam tutup: {jam_tutup} WIB")
        else:
            # Fallback: pertahankan data lama jika ada
            if kode in current_data:
                print(f"  ⚠️  Gagal scrape, pertahankan data lama: {current_data[kode].get('result','?')}")
            else:
                print(f"  ❌ Gagal scrape dan tidak ada data lama untuk {kode}")

    # Update metadata
    current_data["_meta"] = {
        "updated": now.strftime("%Y-%m-%d %H:%M WIB"),
        "date": tgl_str,
        "source": "angkanet-scraper-v2",
        "total": len(current_data) - 1
    }

    with open("result.json", "w") as f:
        json.dump(current_data, f, indent=2, ensure_ascii=False)

    print(f"\n✅ result.json berhasil diperbarui! ({len(current_data)-1} pasaran)")


if __name__ == "__main__":
    update_json()
