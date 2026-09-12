import requests

url = "https://paper-api.alpaca.markets/v2/positions"

headers = {
    "accept": "application/json"
}

# we can just test if requests is available
print("Requests module imported ok")
