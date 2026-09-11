import urllib.request

url = 'https://raw.githubusercontent.com/lth-elm/TradingView-Webhook-Trading-Bot/main/README.md'
try:
    response = urllib.request.urlopen(url)
    data = response.read().decode('utf-8')
    with open('github_readme.md', 'w', encoding='utf-8') as f:
        f.write(data)
    print("Download success. Lines:", len(data.split('\n')))
except Exception as e:
    print("Error:", e)
