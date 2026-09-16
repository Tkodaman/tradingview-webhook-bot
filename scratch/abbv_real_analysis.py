import yfinance as yf
import pandas as pd
import numpy as np

def calculate_rsi(data, window=14):
    delta = data['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

ticker = 'ABBV'
stock = yf.Ticker(ticker)
hist = stock.history(period='6mo')

if not hist.empty:
    hist['RSI'] = calculate_rsi(hist)
    hist['SMA_50'] = hist['Close'].rolling(window=50).mean()
    hist['SMA_200'] = hist['Close'].rolling(window=200).mean()
    
    last_close = hist['Close'].iloc[-1]
    last_rsi = hist['RSI'].iloc[-1]
    sma_50 = hist['SMA_50'].iloc[-1]
    sma_200 = hist['SMA_200'].iloc[-1]
    
    print(f'LAST_CLOSE={last_close:.2f}')
    print(f'RSI={last_rsi:.2f}')
    print(f'SMA_50={sma_50:.2f}')
    print(f'SMA_200={sma_200:.2f}')
    
    # 52 week high/low
    info = stock.info
    print(f"52W_HIGH={info.get('fiftyTwoWeekHigh', 'N/A')}")
    print(f"52W_LOW={info.get('fiftyTwoWeekLow', 'N/A')}")
else:
    print('NO_DATA')
