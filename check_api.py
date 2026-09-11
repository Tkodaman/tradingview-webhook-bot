import urllib.request
try:
    with urllib.request.urlopen("http://127.0.0.1:8000/api/matrix") as response:
        print("Matrix response:", response.read().decode('utf-8')[:500])
except Exception as e:
    print("Error fetching matrix:", e)
