from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List

class Settings(BaseSettings):
    passphrase: str = "secret_key"
    trading_mode: str = "PAPER" # PAPER or LIVE (Alpaca Sandbox vs Real)
    active_broker: str = "ALPACA" # ALPACA, INTERACTIVE_BROKERS, MIDAS
    allowed_ips: str = "127.0.0.1,localhost,testclient,52.89.214.238,34.212.75.30,54.218.53.128,52.32.178.7"
    
    # Alpaca API Credentials
    alpaca_api_key: str = ""
    alpaca_secret_key: str = ""
    
    # Risk Parameters (Esnetilmiş Aktif İşlem Modu)
    max_risk_score_allowed: float = 88.0 # Tavan risk skoru esnetildi
    high_risk_threshold: float = 65.0 # Pozisyon küçültme eşiği yükseltildi
    moderate_risk_threshold: float = 45.0
    
    # Position Sizing
    max_capital_per_trade_pct: float = 10.0 # Max 10% of portfolio per trade ($100 @ $1,000 kasa)
    base_portfolio_size: float = 1000.0 # Başlangıç Kasa: $1,000.00 (Kesin Taban)
    
    # Circuit Breakers & Hard Rules
    flash_crash_volatility_limit: float = 8.0 # Volatilite kilidi %8.0
    volume_anomalies_filter: bool = True  # Hacimsiz sahte kırılım (false breakout) filtresi AKTİF
    volume_anomaly_ratio_threshold: float = 1.2 # Vol.Ratio < 1.2 = BLOK (eski: 0.5)
    macro_event_pause_minutes: int = 5
    
    # Analyzer Agent Weights
    weight_technical: float = 0.40
    weight_macro: float = 0.35
    weight_sentiment: float = 0.25

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    @property
    def get_allowed_ips_list(self) -> List[str]:
        return [ip.strip() for ip in self.allowed_ips.split(",")]

settings = Settings()
