import urllib.request
import json
try:
    req = urllib.request.Request("http://localhost:8000/api/market/live-matrix")
    with urllib.request.urlopen(req) as response:
        content = response.read().decode('utf-8')
        print("Live matrix response:")
        print(content[:500])
except Exception as e:
    print("Error:", e)
