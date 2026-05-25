import json
from datetime import datetime

# Simulasi data agar workflow berhasil dulu
data = {
    "Hongkong Pools": {
        "latest_result": "4509",
        "history": ["4509", "8730", "4851"],
        "last_updated": str(datetime.now())
    }
}

with open("result.json", "w") as f:
    json.dump(data, f, indent=2)

print("✅ Result saved successfully!")
