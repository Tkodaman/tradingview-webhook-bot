from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Optional, Dict, Any, List

class WebhookSignal(BaseModel):
    passphrase: Optional[str] = None
    security_token: Optional[str] = None
    timestamp_ms: int = Field(..., description="Milisaniye cinsinden TradingView çıkış zamanı")
    action: str = Field(..., description="BUY, SELL, CLOSE, HOLD")
    symbol: str = Field(..., min_length=2, description="İşlem paritesi")
    quantity: float = Field(default=1.0, gt=0, description="Dinamik lot/kontrat")
    price: float = Field(..., gt=0, description="Emir tetiklenme fiyatı")
    stop_loss: Optional[float] = None
    take_profit: Optional[float] = None
    account_equity: Optional[float] = Field(default=None)
    market_position: Optional[str] = Field(default=None)
    market_position_size: Optional[float] = Field(default=None)
    order_id: Optional[str] = Field(default=None)
    timeframe: Optional[str] = "15m"
    micro_tf: Optional[str] = Field(default=None)
    macro_tf: Optional[str] = Field(default=None)
    strategy_name: Optional[str] = "TradingView_Strategy"
    indicators: Optional[Dict[str, float]] = Field(default_factory=dict)
    macro_tags: Optional[List[str]] = Field(default_factory=list)

    @field_validator('action')
    @classmethod
    def validate_action(cls, v: str) -> str:
        valid_actions = ["BUY", "SELL", "CLOSE", "HOLD"]
        upper_v = v.upper().strip() if v else ""
        if upper_v not in valid_actions:
            raise ValueError(f"Geçersiz aksiyon (Action): {v}. Beklenen: {valid_actions}")
        return upper_v

    @field_validator('symbol')
    @classmethod
    def validate_symbol(cls, v: str) -> str:
        if not v.isalnum():
            raise ValueError(f"Geçersiz sembol (Symbol): {v}. Sadece alfanumerik olmalıdır.")
        return v.upper()

    @model_validator(mode='after')
    def validate_vital_data(self) -> 'WebhookSignal':
        if not self.timestamp_ms:
            raise ValueError("timestamp_ms eksik! Gecikme ölçümü yapılamaz.")
        if self.price <= 0:
            raise ValueError("Tetikleme fiyatı (price) 0'dan büyük olmalıdır.")
        return self

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
