from typing import Dict, Any, List
from pydantic import BaseModel, Field

class MasterHierarchyData(BaseModel):
    # 1. Order Flow (Highest Priority - 35% Weight)
    order_flow_bullish: bool = Field(True, description="Order Flow imbalance shows buyer dominance")
    order_flow_score: float = Field(85.0, description="Order Flow strength (0-100)")
    
    # 2. Volume Profile (High Priority - 25% Weight)
    volume_profile_support: bool = Field(True, description="Price bouncing from High Volume Node (HVN) or POC")
    volume_profile_score: float = Field(75.0, description="Volume Profile structure strength (0-100)")
    
    # 3. Anchored VWAP (High Priority - 15% Weight)
    anchored_vwap_bullish: bool = Field(True, description="Price above Anchored VWAP from major swing low")
    
    # 4. Price Action (Medium Priority - 12% Weight)
    price_action_bullish: bool = Field(True, description="Higher Highs / Higher Lows or Bullish Engulfing")
    price_action_score: float = Field(70.0, description="Price Action setup quality (0-100)")
    
    # 5. Fibonacci (Low Priority - 8% Weight)
    fibonacci_support: bool = Field(True, description="Price bouncing from 0.5 or 0.618 Golden Ratio")
    
    # 6. Indicators (Lowest Priority - 5% Weight)
    # This represents the output of the 12/24 quantitative indicators engine
    indicator_score: float = Field(65.0, description="Score from generic technical indicators (RSI, MACD etc) (0-100)")

class MasterHierarchyReport(BaseModel):
    total_score: float
    verdict: str
    hierarchy_breakdown: List[Dict[str, Any]]
    bullish_factors: List[str]
    bearish_factors: List[str]

from services.engine.experience_memory_engine import ExperienceMemoryEngine

class MasterHierarchyEngine:
    """
    Evaluates trading setups based on the strict hierarchy:
    Order Flow > Volume Profile > Anchored VWAP >> Price Action > Fibonacci > Indicator
    """
    def evaluate(self, data: MasterHierarchyData) -> MasterHierarchyReport:
        from services.engine.experience_memory_engine import ExperienceMemoryEngine
        # We need to instantiate or import the singleton. It's exported as experience_memory_engine
        from services.engine.experience_memory_engine import experience_memory_engine
        
        score = 0.0
        bullish = []
        bearish = []
        breakdown = []

        try:
            ml_weights = experience_memory_engine.get_dynamic_hierarchy_weights()
        except Exception:
            ml_weights = {}

        def add_component(name: str, passed: bool, base_weight: float, val_score: float = 100.0, desc: str = ""):
            nonlocal score
            
            # YZ İnsiyatifi: ML bazlı dinamik ağırlık çarpanı
            multiplier = ml_weights.get(name, 1.0)
            dynamic_weight = base_weight * multiplier
            
            earned = (val_score / 100.0) * dynamic_weight if passed else 0.0
            score += earned
            
            status = "PASS" if passed else "FAIL"
            if passed:
                bullish.append(f"{name}: {desc} (ML Çarpanı: {multiplier:.2f}x, +{earned:.1f} pts)")
            else:
                bearish.append(f"{name}: Failed / Bearish (0 pts)")
                
            breakdown.append({
                "component": name,
                "status": status,
                "earned_weight": round(earned, 2),
                "base_weight": base_weight,
                "dynamic_weight": round(dynamic_weight, 2),
                "ml_multiplier": multiplier,
                "description": desc
            })

        # 1. Order Flow (35%)
        add_component("Order Flow", data.order_flow_bullish, 35.0, data.order_flow_score, "Buyer dominance in order book & tape")

        # 2. Volume Profile (25%)
        add_component("Volume Profile", data.volume_profile_support, 25.0, data.volume_profile_score, "Strong support at POC/HVN")

        # 3. Anchored VWAP (15%)
        add_component("Anchored VWAP", data.anchored_vwap_bullish, 15.0, 100.0, "Price holding above key institutional AVWAP")

        # 4. Price Action (12%)
        add_component("Price Action", data.price_action_bullish, 12.0, data.price_action_score, "Clean market structure / candlestick patterns")

        # 5. Fibonacci (8%)
        add_component("Fibonacci", data.fibonacci_support, 8.0, 100.0, "Holding Golden Ratio (0.618) or 0.5 Retracement")

        # 6. Technical Indicators (5%)
        indicator_pass = data.indicator_score >= 50.0
        add_component("Indicators", indicator_pass, 5.0, data.indicator_score, "Algorithmic momentum confirmation")

        # Final Evaluation
        final_score = min(100.0, round(score, 1))
        
        if final_score >= 80.0:
            verdict = "STRONG_BUY_CONFIRMED"
        elif final_score >= 60.0:
            verdict = "BUY_APPROVED"
        elif final_score >= 40.0:
            verdict = "NEUTRAL"
        else:
            verdict = "SELL_REJECT"

        return MasterHierarchyReport(
            total_score=final_score,
            verdict=verdict,
            hierarchy_breakdown=breakdown,
            bullish_factors=bullish,
            bearish_factors=bearish
        )

master_hierarchy_engine = MasterHierarchyEngine()
