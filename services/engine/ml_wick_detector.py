import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import yfinance as yf
import datetime

class MLWickDetector:
    def __init__(self, contamination=0.05):
        # We assume 5% of minute-by-minute data points might be extreme anomalies (wicks)
        self.model = IsolationForest(contamination=contamination, random_state=42)
        self.is_trained = False
        
    def train(self, ticker: str):
        """
        Fetches the last 5 days of 1-minute data to learn the 'normal' volatility and volume profile.
        """
        try:
            data = yf.download(ticker, period='5d', interval='1m', progress=False)
            if data.empty:
                return False
                
            # Extract underlying series from multi-index columns if they exist
            if isinstance(data.columns, pd.MultiIndex):
                close = data['Close'][ticker]
                high = data['High'][ticker]
                low = data['Low'][ticker]
                volume = data['Volume'][ticker]
            else:
                close = data['Close']
                high = data['High']
                low = data['Low']
                volume = data['Volume']

            # Feature Engineering
            df = pd.DataFrame()
            df['Price_Change'] = close.pct_change()
            df['Volume_Change'] = volume.pct_change()
            # Handle inf values from volume pct_change where previous volume was 0
            df['Volume_Change'] = df['Volume_Change'].replace([np.inf, -np.inf], 0)
            df['Volatility'] = (high - low) / close
            
            # Drop NaNs
            df = df.dropna()
            
            # Train features: Price Change, Volatility, Volume Change
            X = df[['Price_Change', 'Volatility', 'Volume_Change']].values
            
            self.model.fit(X)
            self.is_trained = True
            return True
        except Exception as e:
            print(f"[ML ERROR] Failed to train Wick Detector on {ticker}: {e}")
            return False

    def is_fake_wick(self, current_pct_change, current_volatility, current_volume_change) -> bool:
        """
        Predicts if the current drop is a fake wick (anomaly) based on learned data.
        Returns True if it's an anomaly (wick), False if it's normal market action (real crash).
        """
        if not self.is_trained:
            # Fail-safe: if not trained, assume it's normal (real drop), keep tight stop
            return False 
            
        # Clean inf inputs
        if np.isinf(current_volume_change):
            current_volume_change = 0.0

        X_test = np.array([[current_pct_change, current_volatility, current_volume_change]])
        prediction = self.model.predict(X_test)
        
        # IsolationForest returns -1 for outliers (anomalies/wicks) and 1 for inliers (normal)
        return prediction[0] == -1
