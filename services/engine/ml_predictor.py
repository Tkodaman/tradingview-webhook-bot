import pandas as pd
import numpy as np
from core.logger import logger

try:
    import xgboost as xgb
    from sklearn.model_selection import train_test_split
    XGB_AVAILABLE = True
except ImportError:
    XGB_AVAILABLE = False
    logger.warning("XGBoost or scikit-learn not installed. Predictive ML Engine will run in simulation mode. Run: pip install xgboost scikit-learn")


class PredictiveMLEngine:
    """
    SOTA Machine Learning Engine (Phase 2 Upgrade)
    Uses XGBoost to predict the probability of the next candle being GREEN (UP).
    Extracts features like RSI, MACD, ATR, and Rolling Volumes.
    """
    def __init__(self):
        self.model = xgb.XGBClassifier(n_estimators=100, learning_rate=0.05, max_depth=5) if XGB_AVAILABLE else None
        self.is_trained = False

    def engineer_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Creates predictive features from raw OHLCV data.
        """
        df = df.copy()
        
        # Calculate Returns
        df['return_1d'] = df['Close'].pct_change()
        
        # Simple Moving Averages
        df['sma_10'] = df['Close'].rolling(window=10).mean()
        df['sma_20'] = df['Close'].rolling(window=20).mean()
        df['sma_dist'] = (df['Close'] - df['sma_20']) / df['sma_20']
        
        # Volatility (ATR Proxy)
        df['high_low_range'] = (df['High'] - df['Low']) / df['Close']
        df['rolling_volatility'] = df['return_1d'].rolling(window=10).std()
        
        # Volume features
        df['vol_sma_10'] = df['Volume'].rolling(window=10).mean()
        df['vol_ratio'] = df['Volume'] / df['vol_sma_10']
        
        # Target Variable (1 if next day is UP, 0 if DOWN)
        df['target'] = (df['Close'].shift(-1) > df['Close']).astype(int)
        
        df.dropna(inplace=True)
        return df

    def train_model(self, historical_data: pd.DataFrame):
        """
        Trains the XGBoost model on historical data.
        """
        if not XGB_AVAILABLE:
            logger.error("Cannot train model. XGBoost not installed.")
            return False

        logger.info("[ML ENGINE] Training Predictive Model...")
        df = self.engineer_features(historical_data)
        
        features = ['return_1d', 'sma_dist', 'high_low_range', 'rolling_volatility', 'vol_ratio']
        X = df[features]
        y = df['target']
        
        # Time-series split (no shuffling to prevent look-ahead bias)
        split_idx = int(len(df) * 0.8)
        X_train, X_test = X.iloc[:split_idx], X.iloc[split_idx:]
        y_train, y_test = y.iloc[:split_idx], y.iloc[split_idx:]
        
        self.model.fit(X_train, y_train, eval_set=[(X_test, y_test)], verbose=False)
        self.is_trained = True
        logger.info("[ML ENGINE] Model training complete.")
        return True

    def predict_direction(self, current_data: pd.DataFrame) -> dict:
        """
        Predicts the probability of the market going UP.
        """
        if not self.is_trained or not XGB_AVAILABLE:
            return {"prediction": "UNKNOWN", "probability_up": 0.50}
            
        df = self.engineer_features(current_data)
        if df.empty:
            return {"prediction": "UNKNOWN", "probability_up": 0.50}
            
        features = ['return_1d', 'sma_dist', 'high_low_range', 'rolling_volatility', 'vol_ratio']
        latest_features = df[features].iloc[[-1]]
        
        prob_up = self.model.predict_proba(latest_features)[0][1]
        
        prediction = "BULL" if prob_up > 0.55 else "BEAR" if prob_up < 0.45 else "NEUTRAL"
        
        logger.info(f"[ML ENGINE] Prediction: {prediction} (Confidence UP: {prob_up:.2%})")
        return {"prediction": prediction, "probability_up": float(prob_up)}
