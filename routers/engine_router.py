from fastapi import APIRouter
from pydantic import BaseModel, Field
from services.engine.auto_runner import tv_auto_runner
from services.engine.autonomous_lab import autonomous_lab
from services.data_ingestion.tradingview_live_client import tradingview_live_client

router = APIRouter()

class AutoRunnerToggleRequest(BaseModel):
    enabled: bool = Field(True, description="Otonom strateji motorunu aç/kapat")
    capital_per_trade: float = Field(100.0, description="İşlem başına kullanılacak bakiye")

@router.post("/auto-runner/toggle")
async def toggle_auto_runner(req: AutoRunnerToggleRequest):
    """
    TradingView ücretli alarmına gerek kalmadan otonom 12-indikatör tarayıcısını başlatır/durdurur.
    """
    tv_auto_runner.is_running = req.enabled
    tv_auto_runner.trade_capital = req.capital_per_trade
    triggers = tv_auto_runner.evaluate_live_market_and_trigger() if req.enabled else []
    return {
        "status": "success",
        "is_running": tv_auto_runner.is_running,
        "capital_per_trade": tv_auto_runner.trade_capital,
        "immediate_triggers": triggers,
        "message": "Otonom TradingView Canlı Strateji Motoru AKTİF!" if req.enabled else "Otonom Motor Durduruldu."
    }

@router.get("/auto-runner/status")
def get_auto_runner_status():
    """
    7/24 Kesintisiz Otonom Motorun Çalışma Durumu
    """
    triggers = tv_auto_runner.evaluate_live_market_and_trigger() if tv_auto_runner.is_running else []
    return {
        "status": "success",
        "is_running": tv_auto_runner.is_running,
        "scan_interval_seconds": getattr(tv_auto_runner, "scan_interval_seconds", 5),
        "capital_per_trade": tv_auto_runner.trade_capital,
        "recent_triggers": triggers
    }

class AutonomousLabRequest(BaseModel):
    base_capital: float = Field(100.0, description="İşlem başı mikro sermaye ($ / ₺)")
    trial_count: int = Field(50, description="Otonom deneme sayısı")

@router.post("/autonomous-lab/run")
async def run_autonomous_lab_experiment(req: AutonomousLabRequest):
    """
    10-Skill, 12-İndikatör ve Makro Verilerle Otonom $100 Algoritma Havuzu Denemeleri Yığını Çalıştırır
    """
    return autonomous_lab.run_autonomous_experiment_pool(
        base_capital=req.base_capital,
        trial_count=req.trial_count
    )

@router.get("/autonomous-lab/latest")
async def get_latest_autonomous_lab_experiment():
    """
    En son çalıştırılan otonom algoritma havuzu sonuçlarını döndürür
    """
    if not autonomous_lab.last_run_result:
        return autonomous_lab.run_autonomous_experiment_pool(100.0, 50)
    return autonomous_lab.last_run_result

