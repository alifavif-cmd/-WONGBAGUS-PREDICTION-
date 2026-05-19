import requests
from bs4 import BeautifulSoup
import json
import re
import datetime
import urllib3
import base64
import os

# Nonaktifkan peringatan SSL
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# ─────────────────────────────────────────────
# KONFIGURASI — isi sesuai repo kamu
# ─────────────────────────────────────────────
GITHUB_TOKEN  = os.environ.get("GITHUB_TOKEN", "")   # set via env var atau isi langsung
GITHUB_OWNER  = "alifavif-cmd"
GITHUB_REPO   = "-WONGBAGUS-PREDICTION-"
GITHUB_FILE   = "result.json"                         # path di dalam repo
GITHUB_BRANCH = "main"                                # atau "master"
# ─────────────────────────────────────────────

BASE_URL = "https://159.65.133.131"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

PASARAN_CONFIG = {
    "hk":   ("/data-pengeluaran-togel-hongkong-pools/", "Hongkong",      "23:00"),
    "hkl":  ("/data-pengeluaran-togel-hklotto/",        "HK Lotto",      "23:00"),
    "sgp":  ("/data-pengeluaran-togel-singapore/",      "Singapore",     "17:40"),
    "sdy":  ("/data-pengeluaran-togel-sydney-pools/",   "Sydney Pools",  "13:45"),
    "sdl":  ("/data-pengeluaran-togel-sdlotto/",        "Sydney Lotto",  "13:45"),
    "kam":  ("/data-pengeluaran-togel-magnum-cambodia/","Kamboja",       "11:50"),
    "bull": ("/data-pengeluaran-togel-bullseye/",       "Bullseye NZ",   "13:10"),
    "chn":  ("/data-pengeluaran-togel-chinapools/",     "China Pools",   "15:30"),
    "jpn":  ("/data-pengeluaran-togel-japan/",          "Japan",         "17:20"),
    "twn":  ("/data-pengeluaran-togel-taiwan/",         "Taiwan",        "20:45"),
}


# ═══════════════════════════════════════
# SCRAPING
# ═══════════════════════════════════════

def scrape_pasaran(path):
    """
    Ambil result 4-digit terakhir dari halaman Angkanet.
    Return: (result_str | None, is_pending_bool)
    """
    url = BASE_URL + path
    try:
        resp = requests.get(url, headers=HEADERS, timeout=15, verify=False)
        if resp.status_code != 200:
            print(f"  [GAGAL] HTTP {resp.status_code} - {url}")
            return None, False

        soup = BeautifulSoup(resp.text, "html.parser")

        # Prioritaskan tabel result jika ada
        result_cell = None
        for td in soup.find_all("td"):
            txt = td.get_text(strip=True)
            if re.match(r"^\d{4}$", txt) or txt.lower() == "xxxx":
                result_cell = txt

        if result_cell is None:
            # Fallback: scan semua teks
            text = soup.get_text(separator=" ")
            tokens = re.findall(r"\b(\d{4}|xxxx)\b", text, re.IGNORECASE)
            if not tokens:
                print(f"  [KOSONG] Tidak ada token 4-digit - {url}")
                return None, False
            result_cell = tokens[-1]

        is_pending = result_cell.lower() == "xxxx"

        # Cari angka valid terakhir
        text = soup.get_text(separator=" ")
        all_tokens = re.findall(r"\b(\d{4}|xxxx)\b", text, re.IGNORECASE)
        valid = [t for t in all_tokens if t.lower() != "xxxx"]

        if not valid:
            return None, is_pending

        return valid[-1], is_pending

    except Exception as e:
        print(f"  [ERROR] {e} - {url}")
        return None, False


def is_already_out(jam_tutup_str):
    now = datetime.datetime.now()
    h, m = map(int, jam_tutup_str.split(":"))
    tutup = now.replace(hour=h, minute=m, second=0, microsecond=0)
    return now >= tutup


# ═══════════════════════════════════════
# GITHUB PUSH
# ═══════════════════════════════════════

def get_file_sha():
    """Ambil SHA file existing di repo (dibutuhkan untuk update)."""
    api_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{GITHUB_FILE}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }
    params = {"ref": GITHUB_BRANCH}
    try:
        resp = requests.get(api_url, headers=headers, params=params, timeout=10)
        if resp.status_code == 200:
            return resp.json().get("sha")
        elif resp.status_code == 404:
            return None  # file belum ada, akan dibuat baru
        else:
            print(f"  [GH-SHA] HTTP {resp.status_code}: {resp.text[:200]}")
            return None
    except Exception as e:
        print(f"  [GH-SHA ERROR] {e}")
        return None


def push_to_github(json_data: dict):
    """Commit + push result.json ke GitHub Pages repo."""
    if not GITHUB_TOKEN:
        print("  ⚠️  GITHUB_TOKEN tidak di-set, skip push ke GitHub.")
        return False

    api_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/contents/{GITHUB_FILE}"
    headers = {
        "Authorization": f"token {GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json"
    }

    content_str = json.dumps(json_data, indent=2, ensure_ascii=False)
    content_b64 = base64.b64encode(content_str.encode("utf-8")).decode("utf-8")

    now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M WIB")
    sha = get_file_sha()

    payload = {
        "message": f"Auto-update result.json | {now_str}",
        "content": content_b64,
        "branch": GITHUB_BRANCH,
    }
    if sha:
        payload["sha"] = sha  # diperlukan untuk update file existing

    try:
        resp = requests.put(api_url, headers=headers, json=payload, timeout=15)
        if resp.status_code in (200, 201):
            action = "diperbarui" if sha else "dibuat baru"
            print(f"  ✅ result.json berhasil {action} di GitHub!")
            return True
        else:
            print(f"  ❌ GitHub API error {resp.status_code}: {resp.text[:300]}")
            return False
    except Exception as e:
        print(f"  [GH-PUSH ERROR] {e}")
        return False


# ═══════════════════════════════════════
# MAIN
# ═══════════════════════════════════════

def update_json():
    # Load lokal jika ada
    try:
        with open("result.json", "r") as f:
            current_data = json.load(f)
        print("result.json lokal loaded.")
    except Exception:
        current_data = {}
        print("result.json tidak ditemukan, mulai kosong.")

    now = datetime.datetime.now()
    tgl_str  = now.strftime("%d/%m")
    time_str = now.strftime("%H:%M WIB")

    print(f"\n=== Scrape {len(PASARAN_CONFIG)} pasaran | {now.strftime('%d/%m/%Y %H:%M WIB')} ===\n")

    for kode, (path, nama, jam_tutup) in PASARAN_CONFIG.items():
        print(f"Scraping [{kode.upper()}] {nama}...")
        result, is_pending = scrape_pasaran(path)
        sudah_waktunya = is_already_out(jam_tutup)

        if result:
            status = "belum" if (is_pending or not sudah_waktunya) else "sudah"
            current_data[kode] = {
                "result": result,
                "tgl":     tgl_str,
                "status":  status,
                "updated": time_str,
                "name":    nama,
                "jam":     jam_tutup
            }
            flag = "⏳ BELUM" if status == "belum" else "✅ SUDAH"
            print(f"  {flag} | {result} | tutup {jam_tutup}")
        else:
            if kode in current_data:
                print(f"  ⚠️  Gagal scrape, pertahankan lama: {current_data[kode].get('result','?')}")
            else:
                print(f"  ❌ Gagal & tidak ada data lama untuk {kode}")

    current_data["_meta"] = {
        "updated": now.strftime("%Y-%m-%d %H:%M WIB"),
        "date":    tgl_str,
        "source":  "angkanet-scraper-v3",
        "total":   len(current_data) - 1
    }

    # Simpan lokal — GitHub Actions yang handle commit & push via git
    with open("result.json", "w") as f:
        json.dump(current_data, f, indent=2, ensure_ascii=False)
    print(f"\n💾 result.json disimpan lokal ({len(current_data)-1} pasaran)")
    print("📤 Push ke GitHub dilakukan oleh step 'Commit & push' di workflow.")


if __name__ == "__main__":
    update_json()
