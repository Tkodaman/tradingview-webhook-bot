import urllib.request
import json

req = urllib.request.Request("http://127.0.0.1:8000/api/positions/active")
try:
    with urllib.request.urlopen(req) as response:
        data = json.loads(response.read().decode('utf-8'))
        positions = data.get("active_positions", [])
        print(f"API returned {len(positions)} positions.")
        for p in positions:
            print(f"- {p['symbol']}")
except Exception as e:
    print(f"Error: {e}")
