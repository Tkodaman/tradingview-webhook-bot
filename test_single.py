import urllib.request
import urllib.error
try:
    req = urllib.request.Request("http://localhost:8000/api/positions/active")
    with urllib.request.urlopen(req) as response:
        print("Success:", response.read().decode('utf-8'))
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code, e.reason)
    print("Response Body:", e.read().decode('utf-8'))
except Exception as e:
    print("Error:", e)
