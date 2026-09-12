from pydantic import BaseModel, Field
from typing import Optional, Dict, Any, List

class WebhookSignal(BaseModel):
    passphrase: str
    security_token: Optional[str] = None
    timestamp_ms: Optional[int] = Field(default=None, description="Milisaniye cinsinden TradingView çıkış zamanı")
    action: str = Field(default="BUY", description="BUY, SELL, CLOSE, HOLD (Büyük/Küçük harf duyarsız)")
    symbol: str
    quantity: float = Field(default=1.0, gt=0, description="TradingView tarafından hesaplanan dinamik lot/kontrat")
    price: float = Field(default=0.0, description="Emir tetiklenme fiyatı")
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    account_equity: Optional[float] = Field(default=None, description="TradingView hesap bakiyesi / sermayesi")
    market_position: Optional[str] = Field(default=None, description="long, short veya flat")
    market_position_size: Optional[float] = Field(default=None, description="Mevcut toplam pozisyon büyüklüğü")
    order_id: Optional[str] = Field(default=None, description="Strateji emir kimliği")
    timeframe: Optional[str] = "15m"
    micro_tf: Optional[str] = Field(default=None, description="Tetikleyici alt zaman dilimi (10m, 15m, 30m)")
    macro_tf: Optional[str] = Field(default=None, description="Makro trend zaman dilimi (45m, 75m, 120m)")
    strategy_name: Optional[str] = "TradingView_Strategy"
    indicators: Optional[Dict[str, float]] = Field(default_factory=dict)
    macro_tags: Optional[List[str]] = Field(default_factory=list)

    @classmethod
    def validate_action(cls, v: str) -> str:
        return v.upper() if v else "BUY"

class RiskAnalysisResult(BaseModel):
    symbol: str
    action: str
    raw_risk_score: float # 0 - 100
    risk_level: str # LOW, MODERATE, HIGH, CRITICAL
    passed_hard_rules: bool
    rejection_reasons: List[str] = []
    adjusted_quantity: float
    confidence_score: float # -100 to +100
    technical_score: float
    macro_score: float
    sentiment_score: float
    hard_rule_triggers: List[str] = []
    timestamp: str
