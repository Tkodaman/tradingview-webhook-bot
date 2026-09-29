import urllib.request
import json
import sys

API_KEY = "tc_live_fwiknvr71Xjb8pOjcqvTzNDHPpSo-ZgRHzFkFuBX6Nc"
URL = "https://tokens.deployapp.space/v1/chat/completions"

headers = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {API_KEY}"
}

data = {
    "model": "cx/gpt-5.6-sol",
    "messages": [{"role": "user", "content": "astra 6"}],
    "max_tokens": 2000,
    "stream": False
}

req = urllib.request.Request(URL, data=json.dumps(data).encode(), headers=headers)

try:
    with urllib.request.urlopen(req) as resp:
        raw_response = resp.read().decode('utf-8')
        response_data = json.loads(raw_response)
        reply = response_data['choices'][0]['message']['content']
        print(reply)
except urllib.error.HTTPError as e:
    print(f"API Error: {e.code} - {e.read().decode()}")
except Exception as e:
    print(f"Error: {e}")
