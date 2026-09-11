import urllib.request
import urllib.error
try:
    req = urllib.request.Request("http://localhost:8000/")
    with urllib.request.urlopen(req) as response:
        content = response.read()
        print("First 100 bytes:", content[:100])
except Exception as e:
    print("Error:", e)
