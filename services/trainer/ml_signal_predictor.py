"""
RandomForest ML Sinyal Tahmin Modeli
Scikit-learn tabanli ikili siniflandirici: KAR (1) / ZARAR (0)
- Her pozisyon kapandiginda egitim verisi birikir (SQLite)
- 30+ kayit sonrasi model otomatik egitilir
- Her 50 yeni islemde model yeniden egitilir
- Tahmin skoru < 0.55 -> BLOCK, > 0.70 -> lot %20 artir
"""
import os
import json
import time
from typing import Optional, Tuple, List, Dict, Any
from core.logger import logger

# Scikit-learn ihtiyatli import — yuklu degilse sessizce devredisi
try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    import numpy as np
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logger.warning("[ML MODEL] scikit-learn/numpy yuklu degil. ML ozelligi devre disi. 'pip install scikit-learn numpy' calistirin.")


TRAINING_DATA_FILE = "ml_training_data.json"
MODEL_MIN_SAMPLES = 30       # Min ornek sayisi
RETRAIN_EVERY_N = 50         # Her N yeni islemde yeniden egit
BLOCK_THRESHOLD = 0.55       # Bu skore altinda BLOCK
REWARD_THRESHOLD = 0.70      # Bu skore ustunde lot artisi


class MLSignalPredictor:
    """
    Kapanan pozisyonlardan otomatik ogrenip gelecek sinyalleri filtreleyen ML modeli.
    """

    def __init__(self):
        self._model: Optional[Any] = None
        self._scaler: Optional[Any] = None
        self._training_data: List[Dict] = []
        self._samples_since_last_train: int = 0
        self._is_trained: bool = False
        self._load_training_data()

    def _load_training_data(self):
        try:
            if os.path.exists(TRAINING_DATA_FILE):
                with open(TRAINING_DATA_FILE, "r", encoding="utf-8") as f:
                    self._training_data = json.load(f)
                logger.info(f"[ML MODEL] {len(self._training_data)} egitim ornegi yuklendi.")
                if len(self._training_data) >= MODEL_MIN_SAMPLES:
                    self._train()
        except Exception as e:
            logger.warning(f"[ML MODEL] Egitim verisi yuklenemedi: {e}")

    def _save_training_data(self):
        try:
            with open(TRAINING_DATA_FILE, "w", encoding="utf-8") as f:
                json.dump(self._training_data[-2000:], f)  # Son 2000 ornek sakla
        except Exception as e:
            logger.warning(f"[ML MODEL] Egitim verisi kaydedilemedi: {e}")

    def _extract_features(self, indicators: Dict[str, Any], context: Dict[str, Any] = None) -> List[float]:
        """Indikatörlerden feature vektoru cikar."""
        ctx = context or {}
        from datetime import datetime
        hour = datetime.now().hour
        day_of_week = datetime.now().weekday()

        features = [
            float(indicators.get("rsi", 50.0)),
            float(indicators.get("macd", 0.0)),
            float(indicators.get("volume_ratio", 1.0)),
            float(indicators.get("adx", 25.0)),
            float(indicators.get("atr_pct", 1.5)),
            float(indicators.get("stoch_k", 50.0)),
            1.0 if indicators.get("ema_golden_cross", False) else 0.0,
            1.0 if indicators.get("supertrend_bullish", True) else 0.0,
            float(indicators.get("mfi", 50.0)),
            float(indicators.get("z_score", 0.0)),
            float(indicators.get("hurst_exponent", 0.5)),
            float(indicators.get("cmf", 0.0)),
            float(indicators.get("change_pct", 0.0)),
            float(ctx.get("fear_greed_score", 50.0)),
            float(hour),
            float(day_of_week),
        ]
        return features

    def record_trade_result(
        self,
        symbol: str,
        indicators: Dict[str, Any],
        pnl: float,
        context: Dict[str, Any] = None,
    ):
        """Kapanan bir islemin sonucunu egitim verisine ekle."""
        if not ML_AVAILABLE:
            return

        label = 1 if pnl > 0 else 0
        features = self._extract_features(indicators, context)

        sample = {
            "symbol": symbol,
            "features": features,
            "label": label,
            "pnl": pnl,
            "timestamp": time.time(),
        }
        self._training_data.append(sample)
        self._samples_since_last_train += 1
        self._save_training_data()

        logger.info(f"[ML MODEL] {symbol} egitim ornegi eklendi (label={label}, pnl={pnl:.2f}). Toplam: {len(self._training_data)}")

        # Yeterli ornekse egit
        if len(self._training_data) >= MODEL_MIN_SAMPLES and (
            not self._is_trained or self._samples_since_last_train >= RETRAIN_EVERY_N
        ):
            self._train()

    def _train(self):
        """Toplanan verilerle modeli egit."""
        if not ML_AVAILABLE or len(self._training_data) < MODEL_MIN_SAMPLES:
            return
        try:
            X = np.array([s["features"] for s in self._training_data])
            y = np.array([s["label"] for s in self._training_data])

            self._scaler = StandardScaler()
            X_scaled = self._scaler.fit_transform(X)

            self._model = RandomForestClassifier(
                n_estimators=100,
                max_depth=6,
                min_samples_leaf=3,
                random_state=42,
                class_weight="balanced",
            )
            self._model.fit(X_scaled, y)
            self._is_trained = True
            self._samples_since_last_train = 0

            win_rate = float(y.mean()) * 100
            logger.info(
                f"[ML MODEL] Model egitildi! {len(X)} ornek | Tarihsel win-rate: %{win_rate:.1f}"
            )
        except Exception as e:
            logger.error(f"[ML MODEL] Egitim hatasi: {e}")

    def predict(
        self, symbol: str, indicators: Dict[str, Any], context: Dict[str, Any] = None
    ) -> Tuple[float, str, float]:
        """
        Sinyal icin kazanma olasiligi tahmini yap.

        Donus: (win_probability, action, lot_multiplier)
          - win_probability: 0.0 - 1.0
          - action: "EXECUTE" / "BLOCK" / "REDUCE"
          - lot_multiplier: 0.0 (block) / 1.0 (normal) / 1.2 (reward)
        """
        if not ML_AVAILABLE or not self._is_trained or self._model is None:
            # Model hazir degil — sey yapma, gecir
            return 0.5, "PASS_NO_MODEL", 1.0

        try:
            features = self._extract_features(indicators, context)
            X = np.array([features])
            X_scaled = self._scaler.transform(X)
            prob = float(self._model.predict_proba(X_scaled)[0][1])  # Kazanma olasiligi

            if prob < BLOCK_THRESHOLD:
                action = "BLOCK"
                lot_mult = 0.0
                logger.info(f"[ML MODEL] {symbol} BLOKE: Kazanma olasiligi %{prob*100:.1f} < %{BLOCK_THRESHOLD*100:.0f}")
            elif prob >= REWARD_THRESHOLD:
                action = "EXECUTE_REWARD"
                lot_mult = 1.2
                logger.info(f"[ML MODEL] {symbol} ODULLU EXECUTE: Kazanma olasiligi %{prob*100:.1f} — lot +%20")
            else:
                action = "EXECUTE"
                lot_mult = 1.0

            return prob, action, lot_mult

        except Exception as e:
            logger.warning(f"[ML MODEL] Tahmin hatasi: {e}. Geciriliyor.")
            return 0.5, "PASS_ERROR", 1.0

    def get_status(self) -> Dict[str, Any]:
        win_count = sum(1 for s in self._training_data if s["label"] == 1)
        total = len(self._training_data)
        return {
            "is_trained": self._is_trained,
            "ml_available": ML_AVAILABLE,
            "training_samples": total,
            "win_rate_historical": round(win_count / total * 100, 1) if total > 0 else 0.0,
            "samples_until_next_train": max(0, RETRAIN_EVERY_N - self._samples_since_last_train),
            "min_samples_needed": MODEL_MIN_SAMPLES,
        }


ml_predictor = MLSignalPredictor()
