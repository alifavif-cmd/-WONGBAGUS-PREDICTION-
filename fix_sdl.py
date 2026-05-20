"""
fix_sdl.py — Patch result.json: ganti SDL 2572 → 1864
Jalankan sekali di repo yang sama dengan result.json
"""
import json

FIXES = {
    'sdl': '1864',   # Sydney Lotto 20-05-2026
}

with open('result.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

for key, correct_result in FIXES.items():
    old = data.get(key, {}).get('result', '???')
    if key in data:
        data[key]['result'] = correct_result
        data[key]['status'] = 'sudah'
        print(f"[{key.upper()}] {old} → {correct_result} ✓")
    else:
        print(f"[{key.upper()}] tidak ditemukan di result.json")

with open('result.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print("\nresult.json berhasil dipatch!")
