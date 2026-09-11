import urllib.request
try:
    req = urllib.request.Request("http://localhost:8000/")
    with urllib.request.urlopen(req) as response:
        content = response.read()
        print("First 20 bytes:", list(content[:20]))
except Exception as e:
    print("Error:", e)
