import requests
import json
import time
import os
from bs4 import BeautifulSoup

# Konfigurasi
OUTPUT_FILE = 'result.json'
# Daftar pasaran bisa diambil dari konfigurasi atau hardcode sesuai kebutuhan
# Contoh struktur data pasaran (sesuaikan dengan logika asli Anda)
MARKETS = [
    {"name": "Hongkong Pools", "url": "https://angkanet18.com/data-pengeluaran-togel-hongkong-pools/"},
    {"name": "Singapore Pools", "url": "https://angkanet18.com/data-pengeluaran-togel-singapore-pools/"},
    # Tambahkan pasaran lainnya di sini...
]

def fetch_html(url):
    """Mengambil konten HTML dari URL."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    try:
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return None

# --- FUNGSI BARU YANG DIGABUNGKAN & DIOPTIMALKAN ---
def extract_result_and_rows(html_content):
    """
    Mengambil hasil utama dan semua baris data dalam SATU kali parsing.
    Menggunakan parser 'lxml' untuk kecepatan maksimal (3-5x lebih cepat dari html.parser).
    
    Returns:
        tuple: (result_data, rows_list)
    """
    if not html_content:
        return None, []

    # Parsing SATU KALI saja dengan lxml
    # Pastikan lxml sudah diinstall: pip install lxml
    soup = BeautifulSoup(html_content, 'lxml')
    
    result_data = None
    rows_list = []

    try:
        # --- LOGIKA EKSTRAKSI HASIL UTAMA ---
        # Sesuaikan selector ini dengan struktur HTML situs target Anda
        # Contoh: Mencari div dengan class tertentu yang berisi angka terbaru
        main_result_div = soup.find('div', class_='result-main') # Ganti dengan class/id yang benar
        if main_result_div:
            # Ekstrak teks atau atribut tertentu
            result_data = main_result_div.get_text(strip=True)
        
        # Jika struktur berbeda, coba cari elemen spesifik lainnya
        if not result_data:
            # Contoh fallback: cari input field atau span tertentu
            input_field = soup.find('input', {'id': 'result_value'})
            if input_field:
                result_data = input_field.get('value')

        # --- LOGIKA EKSTRAKSI SEMUA BARIS (PAITO/HISTORI) ---
        # Contoh: Mencari tabel dengan id tertentu
        table = soup.find('table', class_='paito-table') # Ganti dengan class/id yang benar
        if table:
            tbody = table.find('tbody') or table
            trs = tbody.find_all('tr')
            
            for tr in trs:
                # Ekstrak semua kolom (td) dalam baris tersebut
                cols = [td.get_text(strip=True) for td in tr.find_all('td')]
                if cols: # Pastikan baris tidak kosong
                    rows_list.append(cols)
                    
    except Exception as e:
        print(f"Error during combined extraction: {e}")
        return None, []

    return result_data, rows_list


# --- STUB FUNGSI LAMA (Redirect ke fungsi baru) ---
# Fungsi ini tetap ada agar jika ada bagian kode lain yang belum diupdate
# tidak langsung crash, tapi akan menggunakan logika baru yang efisien.

def extract_result(html_content):
    """
    DEPRECATED: Redirects to extract_result_and_rows.
    Hanya mengembalikan bagian 'result' dari fungsi gabungan.
    """
    result, _ = extract_result_and_rows(html_content)
    return result

def extract_all_rows(html_content):
    """
    DEPRECATED: Redirects to extract_result_and_rows.
    Hanya mengembalikan bagian 'rows' dari fungsi gabungan.
    """
    _, rows = extract_result_and_rows(html_content)
    return rows


def main():
    all_results = {}
    
    print("Memulai proses scraping...")
    
    for market in MARKETS:
        name = market['name']
        url = market['url']
        
        print(f"Processing: {name}...")
        
        # 1. Fetch HTML
        html = fetch_html(url)
        
        if html:
            # 2. Extract Data (Hanya 1x parse per halaman)
            result, rows = extract_result_and_rows(html)
            
            all_results[name] = {
                "latest_result": result,
                "history": rows,
                "last_updated": time.strftime("%Y-%m-%d %H:%M:%S")
            }
            print(f"Success: {name}")
        else:
            print(f"Failed: {name}")
            
        # Jeda singkat agar tidak membebani server target
        time.sleep(1)

    # 3. Simpan ke JSON
    try:
        with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
            json.dump(all_results, f, ensure_ascii=False, indent=4)
        print(f"Data berhasil disimpan ke {OUTPUT_FILE}")
    except Exception as e:
        print(f"Error saving file: {e}")

if __name__ == "__main__":
    main()
