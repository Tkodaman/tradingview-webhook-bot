from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import List
import json
import os

RISK_MODE_STATE_FILE = "risk_mode_state.json"

class Settings(BaseSettings):
    passphrase: str
    trading_mode: str = "PAPER" # PAPER or LIVE (Alpaca Sandbox vs Real)
    active_broker: str = "ALPACA" # ALPACA, INTERACTIVE_BROKERS, MIDAS
    allowed_ips: str = "127.0.0.1,localhost,testclient,52.89.214.238,34.212.75.30,54.218.53.128,52.32.178.7"
    trusted_proxy_ips: str = "127.0.0.1,localhost"
    webhook_security_token: str = ""
    
    # Alpaca API Credentials
    alpaca_api_key: str = ""
    alpaca_secret_key: str = ""
    alpaca_extended_hours: bool = True # Piyasa öncesi ve sonrası işlemler aktif
    
    # Risk Parameters (Esnetilmiş Aktif İşlem Modu)
    max_risk_score_allowed: float = 88.0 # Tavan risk skoru esnetildi
    high_risk_threshold: float = 65.0 # Pozisyon küçültme eşiği yükseltildi
    moderate_risk_threshold: float = 45.0
    
    # Position Sizing
    max_capital_per_trade_pct: float = 25.0 # Max 25% of portfolio per trade for aggressive attacks
    base_portfolio_size: float = 5000.0 # Başlangıç Kasa: $5,000.00 (Kesin Taban)
    dynamic_capital_allocation_pct: float = 25.0  # YENİ: Arayüzden değiştirilebilir işlem büyüklüğü (%)
    
    # Circuit Breakers & Hard Rules
    flash_crash_volatility_limit: float = 8.0 # Volatilite kilidi %8.0
    volume_anomalies_filter: bool = True  # Hacimsiz sahte kırılım (false breakout) filtresi AKTİF
    volume_anomaly_ratio_threshold: float = 1.2 # Vol.Ratio < 1.2 = BLOK (eski: 0.5)
    macro_event_pause_minutes: int = 5
    max_internal_signal_age_seconds: float = 20.0  # Otonom (webhook-dışı) sinyallerde izin verilen maksimum veri yaşı
    
    # Analyzer Agent Weights
    weight_technical: float = 0.40
    weight_macro: float = 0.35
    weight_sentiment: float = 0.25

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Dynamic Risk Mode
    current_risk_mode: str = Field("NORMAL", alias="CURRENT_RISK_MODE")

    def apply_risk_mode(self, mode: str):
        self.current_risk_mode = mode.upper()
        if self.current_risk_mode == "SNIPER":
            self.max_risk_score_allowed = 92.0
            self.high_risk_threshold = 82.0
            self.volume_anomaly_ratio_threshold = 1.5
            self.max_capital_per_trade_pct = 10.0
        elif self.current_risk_mode == "AGGRESSIVE":
            self.max_risk_score_allowed = 100.0  # Çok yüksek tolerans (cüretkar saldırı)
            self.high_risk_threshold = 50.0
            self.volume_anomaly_ratio_threshold = 1.2 # Hacim kilidi (Volume Anomaly Guard) eski haline 1.2 olarak ayarlandı
            self.max_capital_per_trade_pct = 30.0 # Bütçenin 1/3'ünü tek işleme basabilir
        elif self.current_risk_mode == "TIGHT":
            self.max_risk_score_allowed = 90.0
            self.high_risk_threshold = 75.0
            self.volume_anomaly_ratio_threshold = 1.5
            self.max_capital_per_trade_pct = 8.0
        elif self.current_risk_mode == "CONSERVATIVE":
            self.max_risk_score_allowed = 80.0
            self.high_risk_threshold = 85.0
            self.volume_anomaly_ratio_threshold = 2.0
            self.max_capital_per_trade_pct = 5.0
        else: # NORMAL
            self.max_risk_score_allowed = 88.0
            self.high_risk_threshold = 65.0
            self.volume_anomaly_ratio_threshold = 1.2
            self.max_capital_per_trade_pct = 10.0
        self._persist_risk_mode()

    def _persist_risk_mode(self):
        # Sunucu yeniden baslasa (reload=True) veya sayfa yenilense bile secili
        # Risk & Frekans Modu kaybolmasin diye diske yazilir.
        try:
            with open(RISK_MODE_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump({"current_risk_mode": self.current_risk_mode}, f)
        except Exception:
            pass

    def load_persisted_risk_mode(self):
        if not os.path.exists(RISK_MODE_STATE_FILE):
            return
        try:
            with open(RISK_MODE_STATE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            saved_mode = data.get("current_risk_mode")
            if saved_mode:
                self.apply_risk_mode(saved_mode)
        except Exception:
            pass

    @property
    def get_allowed_ips_list(self) -> List[str]:
        return [ip.strip() for ip in self.allowed_ips.split(",")]

    @property
    def get_trusted_proxy_ips_list(self) -> List[str]:
        return [ip.strip() for ip in self.trusted_proxy_ips.split(",") if ip.strip()]

settings = Settings()
settings.load_persisted_risk_mode()
