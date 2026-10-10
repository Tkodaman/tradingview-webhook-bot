import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

url = f"https://generativelanguage.googleapis.com/v1beta/models?key={GEMINI_API_KEY}"
try:
    resp = requests.get(url, verify=False, timeout=10)
    data = resp.json()
    if 'models' in data:
        for m in data['models']:
            print(m['name'])
    else:
        print("Response:", data)
except Exception as e:
    print("Error:", e)

