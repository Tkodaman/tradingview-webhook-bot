import random
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Tuple
from core.config import settings
from core.logger import logger

class BotTrainer:
    """
    Bot Eğitimi, Tarihsel Simülasyon ve Risk Ağırlığı Optimizasyon Motoru.
    Piyasa senaryoları (Faiz kararları, şok haberler, volatilite patlamaları, sahte kırılımlar)
    üzerinde stratejiyi eğiterek en iyi risk/kazanç ağırlıklarını kalibre eder.
    """
    def __init__(self):
        self.training_history: List[Dict[str, Any]] = []
        self.best_params = {
            "weight_technical": settings.weight_technical,
            "weight_macro": settings.weight_macro,
            "weight_sentiment": settings.weight_sentiment,
            "max_risk_score_allowed": settings.max_risk_score_allowed,
            "sharpe_ratio": 1.45,
            "win_rate": 68.5,
            "max_drawdown": 4.2
        }

    def load_historical_scenarios_from_memory(self) -> List[Dict[str, Any]]:
        """
        Deneyim hafızasından gerçek geçmiş işlemleri (kâr/zarar, indikatör durumları, duyarlılık) çeker.
        Bunları ML eğitim senaryosu formatına dönüştürür.
        """
        try:
            from services.engine.experience_memory_engine import experience_memory_engine
            history = experience_memory_engine.trade_history
            scenarios = []
            for i, trade in enumerate(history):
                indicators = trade.indicators_at_entry or {}
                
                # Gerçek veriden oku, yoksa makul bir ortalama ata
                volatility = float(indicators.get("volatility", 2.0))
                volume_ratio = float(indicators.get("volume_ratio", 1.2))
                rsi = float(indicators.get("rsi", 50.0))
                sentiment = float(indicators.get("sentiment", 0.0))
                macro_risk = float(indicators.get("macro_risk", 30.0))
                
                # Eğer kayıtlı rejimde belirli kelimeler varsa indikatörleri ona göre tahmini doldur
                regime = str(trade.market_regime).upper()
                if "BOĞA" in regime or "MOMENTUM" in regime:
                    rsi = max(rsi, 55.0)
                    sentiment = max(sentiment, 20.0)
                elif "AYI" in regime or "CRASH" in regime:
                    rsi = min(rsi, 45.0)
                    sentiment = min(sentiment, -20.0)
                    
                scenarios.append({
                    "id": f"real_{trade.trade_id if hasattr(trade, 'trade_id') else i}",
                    "category": "REAL_EXPERIENCE",
                    "action": trade.action,
                    "price": trade.entry_price,
                    "volatility": volatility,
                    "volume_ratio": volume_ratio,
                    "sentiment": sentiment,
                    "macro_risk": macro_risk,
                    "rsi": rsi,
                    "price_change_pct": trade.pnl_pct
                })
            return scenarios
        except Exception as e:
            logger.error(f"[BOT TRAINER] Gerçek tecrübe yüklenirken hata: {e}")
            return []

    def generate_synthetic_historical_scenarios(self, count: int = 500) -> List[Dict[str, Any]]:
        """
        Geçmiş piyasa rejimlerini (Trend, Kriz, Şok Haber, Sahte Kırılım) temsil eden veri seti üretir.
        """
        scenarios = []
        categories = ["NORMAL_TREND", "FED_RATE_DAY", "GEOPOLITICAL_SHOCK", "FLASH_CRASH", "FALSE_BREAKOUT"]
        
        for i in range(count):
            cat = random.choices(categories, weights=[0.45, 0.20, 0.15, 0.10, 0.10])[0]
            action = random.choice(["BUY", "SELL"])
            base_price = 100.0 + random.uniform(-10, 50)
            
            if cat == "NORMAL_TREND":
                volatility = random.uniform(0.8, 2.2)
                volume_ratio = random.uniform(1.1, 2.5)
                sentiment = random.uniform(-10, 40) if action == "BUY" else random.uniform(-40, 10)
                macro_risk = random.uniform(10, 40)
                rsi = random.uniform(45, 65)
                # Beklenen piyasa sonucu: Sinyal yönünde pozitif getiri olasılığı yüksek
                price_change_pct = random.uniform(0.5, 3.5) if random.random() < 0.72 else -random.uniform(0.5, 1.5)
            
            elif cat == "FED_RATE_DAY":
                volatility = random.uniform(2.5, 4.2)
                volume_ratio = random.uniform(1.5, 3.0)
                sentiment = random.uniform(-60, 60)
                macro_risk = random.uniform(60, 90)
                rsi = random.uniform(30, 70)
                price_change_pct = random.uniform(-4.0, 4.0)

            elif cat == "GEOPOLITICAL_SHOCK":
                volatility = random.uniform(3.0, 5.5)
                volume_ratio = random.uniform(1.8, 3.5)
                sentiment = random.uniform(-80, -30)
                macro_risk = random.uniform(75, 98)
                rsi = random.uniform(20, 45)
                price_change_pct = -random.uniform(1.5, 6.0) if action == "BUY" else random.uniform(1.0, 4.0)

            elif cat == "FLASH_CRASH":
                volatility = random.uniform(4.5, 8.0)
                volume_ratio = random.uniform(2.5, 5.0)
                sentiment = random.uniform(-90, -50)
                macro_risk = random.uniform(80, 100)
                rsi = random.uniform(10, 30)
                price_change_pct = -random.uniform(3.0, 10.0)

            elif cat == "FALSE_BREAKOUT":
                volatility = random.uniform(1.0, 2.5)
                volume_ratio = random.uniform(0.2, 0.5) # Düşük hacim
                sentiment = random.uniform(-20, 20)
                macro_risk = random.uniform(30, 50)
                rsi = random.uniform(68, 80)
                price_change_pct = -random.uniform(1.0, 3.0) # Tuzağa düşme

            scenarios.append({
                "id": i,
                "category": cat,
                "action": action,
                "price": base_price,
                "volatility": volatility,
                "volume_ratio": volume_ratio,
                "sentiment": sentiment,
                "macro_risk": macro_risk,
                "rsi": rsi,
                "price_change_pct": price_change_pct
            })
        return scenarios

    def evaluate_strategy_parameters(
        self,
        scenarios: List[Dict[str, Any]],
        w_tech: float,
        w_macro: float,
        w_sent: float,
        max_risk_allowed: float
    ) -> Dict[str, float]:
        """
        Verilen parametre seti için simülasyon çalıştırır ve metrikleri hesaplar.
        """
        capital = 10000.0
        equity_curve = [capital]
        trades = 0
        wins = 0
        losses = 0
        total_pnl = 0.0

        for sc in scenarios:
            # 1. Teknik Risk
            tech_risk = min(100.0, (sc["volatility"] / 4.0) * 100.0 * 0.4 + (80.0 if sc["volume_ratio"] < 0.7 else 20.0) * 0.35 + (70.0 if sc["rsi"] > 75 or sc["rsi"] < 25 else 20.0) * 0.25)
            # 2. Makro Risk
            macro_risk = sc["macro_risk"]
            # 3. Duygu Riski
            sent_risk = max(0.0, min(100.0, (50.0 - (sc["sentiment"] * 0.5))))

            total_risk_score = (tech_risk * w_tech) + (macro_risk * w_macro) + (sent_risk * w_sent)

            # Sert Kurallar
            # Kural A: Tavan risk skoru
            if total_risk_score > max_risk_allowed:
                continue # Emri engelle
            # Kural B: Devre kesici volatilite
            if sc["volatility"] >= settings.flash_crash_volatility_limit:
                continue # Engelle
            # Kural C: Düşük hacimli sahte kırılım
            if sc["volume_ratio"] < 0.5:
                continue # Engelle

            # Dinamik boyutlandırma
            size_multiplier = 0.4 if total_risk_score >= 55.0 else (0.75 if total_risk_score >= 35.0 else 1.0)
            trade_amount = capital * 0.05 * size_multiplier # %5 risk
            
            pnl = trade_amount * (sc["price_change_pct"] / 100.0)
            capital += pnl
            equity_curve.append(capital)
            trades += 1

            if pnl > 0:
                wins += 1
            else:
                losses += 1
            total_pnl += pnl

        returns = np.diff(equity_curve) / equity_curve[:-1] if len(equity_curve) > 1 else np.array([0.0])
        mean_ret = np.mean(returns) if len(returns) > 0 else 0.0
        std_ret = np.std(returns) if len(returns) > 0 and np.std(returns) > 0 else 0.0001
        sharpe = (mean_ret / std_ret) * np.sqrt(252) if std_ret > 0 else 0.0
        
        # Max Drawdown
        peak = np.maximum.accumulate(equity_curve)
        drawdowns = (peak - equity_curve) / peak
        max_dd = float(np.max(drawdowns)) * 100.0 if len(drawdowns) > 0 else 0.0
        win_rate = (wins / trades * 100.0) if trades > 0 else 0.0

        return {
            "trades": trades,
            "wins": wins,
            "losses": losses,
            "win_rate": round(win_rate, 2),
            "final_capital": round(capital, 2),
            "total_pnl": round(total_pnl, 2),
            "total_return_pct": round(((capital - 10000.0) / 10000.0) * 100.0, 2),
            "max_drawdown": round(max_dd, 2),
            "sharpe_ratio": round(sharpe, 2)
        }

    def train_bot(self, iterations: int = 400) -> Dict[str, Any]:
        """
        Gerçek geçmiş verileri ve sentetik verileri harmanlayarak (Data Augmentation) 
        Grid/Randomized Search ile model ağırlıklarını eğitir.
        """
        logger.info("[BOT TRAINING STARTED] Loading real experience and generating synthetic regimes...")
        
        real_scenarios = self.load_historical_scenarios_from_memory()
        
        # Eğer yeterince gerçek işlemimiz yoksa, üzerine sentetik senaryo ekle
        scenarios = real_scenarios.copy()
        if len(scenarios) < 300:
            synthetic_needed = 300 - len(scenarios)
            synthetic_scenarios = self.generate_synthetic_historical_scenarios(count=synthetic_needed)
            scenarios.extend(synthetic_scenarios)
            
        logger.info(f"[BOT TRAINER] Training on {len(real_scenarios)} REAL trades + {len(scenarios)-len(real_scenarios)} SYNTHETIC trades.")
        
        best_score = -999.0
        best_result = {}
        best_weights = {}

        # Parametre arama uzayı
        for _ in range(iterations):
            w_tech = round(random.uniform(0.20, 0.60), 2)
            w_macro = round(random.uniform(0.20, 0.50), 2)
            w_sent = round(max(0.05, 1.0 - (w_tech + w_macro)), 2)
            
            # Normalizasyon
            total_w = w_tech + w_macro + w_sent
            w_tech = round(w_tech / total_w, 2)
            w_macro = round(w_macro / total_w, 2)
            w_sent = round(1.0 - (w_tech + w_macro), 2)

            max_risk = round(random.uniform(65.0, 85.0), 1)

            metrics = self.evaluate_strategy_parameters(scenarios, w_tech, w_macro, w_sent, max_risk)
            
            # Optimizasyon Fonksiyonu: Sharpe * WinRate - MaxDrawdown Penalty
            fitness_score = (metrics["sharpe_ratio"] * 2.0) + (metrics["win_rate"] * 0.1) - (metrics["max_drawdown"] * 0.3)

            if fitness_score > best_score and metrics["trades"] >= 50:
                best_score = fitness_score
                best_result = metrics
                best_weights = {
                    "weight_technical": w_tech,
                    "weight_macro": w_macro,
                    "weight_sentiment": w_sent,
                    "max_risk_score_allowed": max_risk
                }

        # En iyi parametreleri canlı sisteme uygula
        settings.weight_technical = best_weights["weight_technical"]
        settings.weight_macro = best_weights["weight_macro"]
        settings.weight_sentiment = best_weights["weight_sentiment"]
        # Training must never weaken the active risk mode's hard ceiling.
        trained_risk_limit = best_weights["max_risk_score_allowed"]
        if settings.current_risk_mode == "CONSERVATIVE":
            trained_risk_limit = min(trained_risk_limit, 80.0)
        settings.max_risk_score_allowed = trained_risk_limit
        best_weights["max_risk_score_allowed"] = trained_risk_limit

        training_summary = {
            "status": "TRAINING_COMPLETED_SUCCESSFULLY",
            "optimized_weights": best_weights,
            "backtest_performance": best_result,
            "scenarios_tested": len(scenarios),
            "applied_to_live_settings": True
        }

        self.best_params = {**best_weights, **best_result}
        self.training_history.append(training_summary)
        logger.info(f"[BOT TRAINING COMPLETE] Best Weights: {best_weights} | Sharpe: {best_result.get('sharpe_ratio')} | WinRate: {best_result.get('win_rate')}%")

        return training_summary

bot_trainer = BotTrainer()
