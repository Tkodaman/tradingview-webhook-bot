import requests
import urllib3
urllib3.disable_warnings()

try:
    print("Testing without verify=False...")
    res = requests.get("https://api.binance.com/api/v3/ping", timeout=5)
    print("Success:", res.status_code)
except Exception as e:
    print("Failed without verify:", type(e).__name__, e)

try:
    print("\nTesting with verify=False...")
    res = requests.get("https://api.binance.com/api/v3/ping", verify=False, timeout=5)
    print("Success:", res.status_code)
except Exception as e:
    print("Failed with verify=False:", type(e).__name__, e)
