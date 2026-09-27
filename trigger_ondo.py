import requests
import time

payload = {
    'symbol': 'ONDOUSDT',
    'action': 'BUY',
    'price': 0.5477,
    'quantity': 100.0,
    'passphrase': 'Jeliada.1907',
    'timeframe': '15m',
    'timestamp_ms': int(time.time()*1000),
    'indicators': {
        'rsi': 54.2,
        'volume_ratio': 1.09,
        'adx': 25.0
    }
}
try:
    res = requests.post('http://127.0.0.1:8000/webhook', json=payload)
    print(res.status_code, res.text)
except Exception as e:
    print("Error:", e)
