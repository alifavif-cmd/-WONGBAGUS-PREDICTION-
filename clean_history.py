import json
from datetime import datetime

INPUT_FILE = "result.json"
OUTPUT_FILE = "result.json"  # overwrite langsung

# Tanggal minimum yang dianggap valid (ubah sesuai kebutuhan)
MIN_VALID_DATE = "2026-01-01"

with open(INPUT_FILE, "r") as f:
    data = json.load(f)

total_removed = 0
pasaran_affected = []

for key, val in data.items():
    if key == "_meta":
        continue
    if "history" not in val:
        continue

    original = val["history"]
    cleaned = []
    seen_dates = set()

    for entry in original:
        d = entry.get("date", "")
        # Hapus jika tanggal terlalu lama atau duplikat
        if d < MIN_VALID_DATE:
            total_removed += 1
            continue
        if d in seen_dates:
            total_removed += 1
            continue
        seen_dates.add(d)
        cleaned.append(entry)

    if len(cleaned) != len(original):
        pasaran_affected.append(key)

    # Urutkan terbaru di atas
    cleaned.sort(key=lambda x: x["date"], reverse=True)
    val["history"] = cleaned

with open(OUTPUT_FILE, "w") as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"Selesai.")
print(f"Total entry dihapus : {total_removed}")
print(f"Pasaran yang dibersihkan: {pasaran_affected}")
print(f"Disimpan ke: {OUTPUT_FILE}")
