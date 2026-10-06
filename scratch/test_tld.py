from binance.client import Client
print(Client.API_URL)
try:
    c = Client(tld='us')
    print("US ping:", c.ping())
except Exception as e:
    print("US failed:", e)

try:
    c = Client(tld='info')
    print("Info ping:", c.ping())
except Exception as e:
    print("Info failed:", e)
