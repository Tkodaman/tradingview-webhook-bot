import yfinance as yf
import requests
import pandas as pd
from typing import Optional
from core.logger import logger
import time

class MarketDataFetcher:
    """
    Geçmiş OHLCV (Mum) verilerini getiren modül.
    Kripto için Binance API, Hisseler için Yahoo Finance kullanır.
    """
    
    def __init__(self):
        self.binance_url = "https://api.binance.com/api/v3/klines"
        self._cache = {} # Basit önbellek: { "BTCUSDT_15m": (timestamp, DataFrame) }
        self.CACHE_TTL = 300 # 5 dakika

    def get_crypto_data(self, symbol: str, interval: str = "15m", limit: int = 100) -> Optional[pd.DataFrame]:
        """Binance üzerinden OHLCV çeker."""
        # Sembolü Binance formatına çevir (örn: BTCUSD -> BTCUSDT)
        if symbol.endswith("USD") and symbol != "USD":
            symbol = symbol + "T"
            
        cache_key = f"{symbol}_{interval}_{limit}"
        if cache_key in self._cache:
            ts, df = self._cache[cache_key]
            if time.time() - ts < self.CACHE_TTL:
                return df

        params = {
            "symbol": symbol.upper(),
            "interval": interval,
            "limit": limit
        }
        
        try:
            res = requests.get(self.binance_url, params=params, timeout=5)
            if res.status_code == 200:
                data = res.json()
                # Klines format: [Open time, Open, High, Low, Close, Volume, Close time, Quote asset volume, Number of trades, Taker buy base asset volume, Taker buy quote asset volume, Ignore]
                df = pd.DataFrame(data, columns=[
                    "timestamp", "open", "high", "low", "close", "volume", 
                    "close_time", "qav", "num_trades", "tbbav", "tbqav", "ignore"
                ])
                df["timestamp"] = pd.to_datetime(df["timestamp"], unit='ms')
                for col in ["open", "high", "low", "close", "volume"]:
                    df[col] = df[col].astype(float)
                
                df.set_index("timestamp", inplace=True)
                self._cache[cache_key] = (time.time(), df)
                return df
            else:
                logger.warning(f"[DATA FETCHER] Binance {symbol} verisi çekilemedi. Status: {res.status_code}")
                return None
        except Exception as e:
            logger.error(f"[DATA FETCHER] Binance {symbol} bağlantı hatası: {e}")
            return None

    def get_stock_data(self, symbol: str, interval: str = "15m", limit: int = 100) -> Optional[pd.DataFrame]:
        """Yahoo Finance üzerinden OHLCV çeker."""
        # yfinance interval format mapping: "15m" -> "15m", "1h" -> "60m", "1d" -> "1d"
        cache_key = f"{symbol}_{interval}_{limit}"
        if cache_key in self._cache:
            ts, df = self._cache[cache_key]
            if time.time() - ts < self.CACHE_TTL:
                return df

        try:
            ticker = yf.Ticker(symbol.upper())
            # yfinance max period for intraday (like 15m) is 60d
            df = ticker.history(period="60d", interval=interval)
            
            if df.empty:
                logger.warning(f"[DATA FETCHER] Yahoo Finance {symbol} verisi boş döndü.")
                return None
                
            df = df.tail(limit)
            # Sütun isimlerini küçük harf yap
            df.columns = [c.lower() for c in df.columns]
            
            self._cache[cache_key] = (time.time(), df)
            return df
        except Exception as e:
            logger.error(f"[DATA FETCHER] Yahoo Finance {symbol} bağlantı hatası: {e}")
            return None

    def get_ohlcv(self, symbol: str, market_type: str = "CRYPTO", interval: str = "15m", limit: int = 100) -> Optional[pd.DataFrame]:
        """Piyasaya göre uygun OHLCV verisini çeker."""
        if market_type == "CRYPTO":
            return self.get_crypto_data(symbol, interval, limit)
        else:
            return self.get_stock_data(symbol, interval, limit)

data_fetcher = MarketDataFetcher()
