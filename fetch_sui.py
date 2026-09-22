import yfinance as yf
t = yf.Ticker('SUI-USD')
info = t.info
price = info.get('regularMarketPrice', info.get('currentPrice', 0))
ask = info.get('ask', price)
bid = info.get('bid', price)
if ask and bid:
    spread = ask - bid
    spread_pct = (spread / ask) * 100
    print(f"Price: {price}, Ask: {ask}, Bid: {bid}, Spread: {spread:.4f} ({spread_pct:.4f}%)")
else:
    print(f"Price: {price}, Ask/Bid info missing from yfinance.")
