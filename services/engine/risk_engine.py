import numpy as np
import datetime
import pytz
from services.engine.ml_wick_detector import MLWickDetector

# Initialize global ML Wick Detector
_ml_detector = MLWickDetector()
_ml_detector_trained_for = None

class RiskEngine:
    """
    SOTA Dynamic Risk Management Engine (Shadow AI Core)
    Handles Trailing Stops via ATR and Position Sizing via Kelly Criterion.
    """
    
    @staticmethod
    def is_market_open_volatility_window() -> bool:
        """
        Checks if the current time is within the US Market Open volatility window 
        (16:25 to 16:35 Istanbul Time) where algorithmic stop hunting (Sniper Wicks) occurs.
        """
        tz = pytz.timezone('Europe/Istanbul')
        now = datetime.datetime.now(tz)
        
        # Check if it's a weekday
        if now.weekday() >= 5:
            return False
            
        # Market open in Turkey is usually 16:30. Window: 16:25 - 16:35
        # Note: Daylight saving time changes may shift this, assuming 16:30 standard.
        if now.hour == 16 and (25 <= now.minute <= 35):
            return True
        return False
    
    @staticmethod
    def calculate_atr_trailing_stop(current_price: float, atr: float, direction: str = "LONG", asset_type: str = "CRYPTO", ticker: str = None, current_pct_change: float = 0.0, current_volatility: float = 0.0, current_volume_change: float = 0.0) -> float:
        """
        Calculates a dynamic trailing stop based on Average True Range (ATR).
        Direction: "LONG" or "SHORT"
        Asset Type: "CRYPTO" uses wider multiplier (3.5) to avoid Stop Hunting. "STOCK" uses standard (2.0).
        """
        global _ml_detector, _ml_detector_trained_for
        
        # Anti-Stop-Hunt Logic: Widen the spread for Crypto to survive liquidity sweeps
        multiplier = 3.5 if asset_type.upper() == "CRYPTO" else 2.0
        
        # ML Wick Detection Override
        is_wick = False
        if ticker:
            # Train model if not trained for this ticker
            if _ml_detector_trained_for != ticker:
                print(f"[ML] Training Wick Detector for {ticker}...")
                success = _ml_detector.train(ticker)
                if success:
                    _ml_detector_trained_for = ticker
            
            # Predict if current movement is a fake wick
            if _ml_detector.is_trained:
                is_wick = _ml_detector.is_fake_wick(current_pct_change, current_volatility, current_volume_change)
                if is_wick:
                    print(f"[ML-ZIRH] {ticker} icin sahte igne (Stop-Hunt) tespit edildi! Zirh genisletiliyor.")
                    multiplier += 2.0 # Widen stop IMMENSELY for fake wicks
                else:
                    # ML says it's a real trend, tighten the armor to GTFO quickly
                    multiplier = max(1.5, multiplier - 0.5)

        # Fallback to extreme Volatility Override if ML didn't flag it but it's market open
        if not is_wick and RiskEngine.is_market_open_volatility_window():
            multiplier += 1.5
            
        if direction.upper() == "LONG":
            return current_price - (atr * multiplier)
        elif direction.upper() == "SHORT":
            return current_price + (atr * multiplier)
        else:
            raise ValueError("Direction must be 'LONG' or 'SHORT'")

    @staticmethod
    def calculate_kelly_fraction(win_rate: float, win_loss_ratio: float, fraction_multiplier: float = 0.5) -> float:
        """
        Calculates the Kelly Criterion for optimal position sizing.
        Applies the 'Shame Protocol' penalty to fraction_multiplier to mathematically degrade confidence.
        """
        if win_loss_ratio <= 0:
            return 0.0
            
        kelly_perc = win_rate - ((1 - win_rate) / win_loss_ratio)
        
        if kelly_perc <= 0:
            return 0.0
            
        # --- SHAME PROTOCOL INTEGRATION ---
        shame_score = 0
        try:
            import json
            import os
            shame_path = os.path.join(os.path.dirname(__file__), 'shame_protocol.json')
            if os.path.exists(shame_path):
                with open(shame_path, 'r') as f:
                    data = json.load(f)
                    shame_score = data.get('shame_score', 0)
        except Exception:
            pass
            
        # Mathematically degrade confidence (Each shame point reduces multiplier by 1%)
        penalty = shame_score * 0.01
        degraded_multiplier = max(0.01, fraction_multiplier - penalty)
        
        safe_kelly = kelly_perc * degraded_multiplier
        return min(safe_kelly, 0.30)
