import yfinance as yf
t = yf.Ticker('ANET')
i = t.info
h = t.history(period='5d')
print(f"Price: {i.get('currentPrice')}")
print(f"Beta: {i.get('beta')}")
print(f"PE: {i.get('trailingPE')}")
print(f"52w High: {i.get('fiftyTwoWeekHigh')}")
print(h[['Close', 'Volume']])
