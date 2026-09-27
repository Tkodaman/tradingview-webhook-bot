import sys

content = open('services/data_ingestion/tradingview_live_client.py', encoding='utf-8').read()

old_str = '''        columns = [
            "name", "close", "change", "high", "low", "volume",
            "RSI", "MACD.macd", "MACD.signal", "EMA20", "EMA50", "EMA200",
            "ATR", "VWAP", "Stoch.K", "ADX", "Volatility.D", "average_volume_10d_calc",
            "ChaikinMoneyFlow",
            "open"   # ==='''

new_str = '''        columns = [
            "name", "close", "change|15", "high|15", "low|15", "volume|15",
            "RSI|15", "MACD.macd|15", "MACD.signal|15", "EMA20|15", "EMA50|15", "EMA200|15",
            "ATR|15", "VWAP|15", "Stoch.K|15", "ADX|15", "Volatility.D|15", "average_volume_10d_calc|15",
            "ChaikinMoneyFlow|15",
            "open|15"   # ==='''

content = content.replace(old_str, new_str)
open('services/data_ingestion/tradingview_live_client.py', 'w', encoding='utf-8').write(content)
print('Replaced')
