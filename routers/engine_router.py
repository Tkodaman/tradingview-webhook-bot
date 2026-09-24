from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
from typing import List
from services.engine.auto_runner import tv_auto_runner
from services.engine.autonomous_lab import autonomous_lab
from services.data_ingestion.tradingview_live_client import tradingview_live_client
from core.security import verify_ip

router = APIRouter(dependencies=[Depends(verify_ip)])

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
    return {
        "status": "success",
        "is_running": tv_auto_runner.is_running,
        "scan_interval_seconds": getattr(tv_auto_runner, "scan_interval_seconds", 3.0),
        "capital_per_trade": tv_auto_runner.trade_capital if hasattr(tv_auto_runner, 'trade_capital') else 100.0,
        "recent_triggers": []
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

class RiskModeRequest(BaseModel):
    mode: str = Field(..., description="Strateji Modu (AGGRESSIVE, NORMAL, TIGHT, CONSERVATIVE)")

@router.get("/engine/risk-mode")
def get_risk_mode():
    from core.config import settings
    return {
        "status": "success",
        "current_mode": settings.current_risk_mode
    }

@router.post("/engine/risk-mode")
async def set_risk_mode(req: RiskModeRequest):
    from core.config import settings
    from services.market_feed.live_stream import live_trade_manager
    try:
        settings.apply_risk_mode(req.mode)

        # Bir Risk & Frekans Modu secmek, kullanicinin acikca "otonom devral" niyetidir.
        # Her iki otonom yurutme kapisini da acip ani bir degerlendirme dongusu tetikliyoruz.
        tv_auto_runner.is_running = True
        live_trade_manager.auto_trade_enabled = True
        live_trade_manager.save_auto_trade_flag()
        immediate_triggers = tv_auto_runner.evaluate_live_market_and_trigger()

        return {
            "status": "success",
            "message": f"Risk Modu '{settings.current_risk_mode}' olarak güncellendi. Otonom motor AKTİF, anlık tarama yapıldı.",
            "current_mode": settings.current_risk_mode,
            "max_risk_allowed": settings.max_risk_score_allowed,
            "high_risk_threshold": settings.high_risk_threshold,
            "volume_anomaly_ratio_threshold": settings.volume_anomaly_ratio_threshold,
            "max_capital_per_trade_pct": settings.max_capital_per_trade_pct,
            "auto_trade_enabled": live_trade_manager.auto_trade_enabled,
            "immediate_triggers": immediate_triggers,
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

class CapitalAllocationRequest(BaseModel):
    allocation_pct: float = Field(..., description="Kasa üzerinden işlem başına kullanılacak bakiye yüzdesi (örn: 10.0)")

@router.post("/engine/capital-allocation")
async def set_capital_allocation(req: CapitalAllocationRequest):
    from core.config import settings
    import dotenv
    from pathlib import Path
    try:
        # Bellekte güncelle
        settings.dynamic_capital_allocation_pct = req.allocation_pct
        
        # Kalıcı olması için .env dosyasına yaz
        env_path = Path(".env")
        if not env_path.exists():
            env_path.touch()
        dotenv.set_key(str(env_path), "DYNAMIC_CAPITAL_ALLOCATION_PCT", str(req.allocation_pct))
        
        return {
            "status": "success",
            "message": f"Sermaye yönetimi %{req.allocation_pct} olarak güncellendi ve kaydedildi.",
            "dynamic_capital_allocation_pct": settings.dynamic_capital_allocation_pct
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

class BacktestRequest(BaseModel):
    symbols: List[str] = Field(..., description="Sembol listesi (Örn: AAPL, TSLA)")
    timeframe: str = Field("15Min", description="Zaman dilimi: 1Min, 5Min, 15Min, 1Hour, 1Day")
    days_back: int = Field(30, description="Kaç günlük geçmiş veri çekilecek?")

@router.post("/engine/run-backtest")
async def run_backtest_endpoint(req: BacktestRequest):
    try:
        from services.agents.backtest_engine import BacktestEngine
        engine = BacktestEngine(symbols=req.symbols, timeframe=req.timeframe, days_back=req.days_back)
        results = engine.run_sweep()
        return {"status": "success", "data": [r.model_dump() for r in results]}
    except Exception as e:
        import traceback
        logger.error(f"Backtest failed: {e}\n{traceback.format_exc()}")
        return {"status": "error", "message": str(e)}


@router.get("/shadow-trades")
def get_shadow_trades():
    from services.engine.trade_journal_learning import trade_journal_engine
    return {"status": "success", "shadow_trades": trade_journal_engine.shadow_journal_entries}

@router.get("/shadow-cache")
def get_shadow_cache():
    from services.analyzer.agent import analyzer_agent
    return {"status": "success", "shadow_cache": analyzer_agent.shadow_analysis_cache}

class AiModelRequest(BaseModel):
    provider: str = Field(..., description="LLM Provider: 'openai' veya 'gemini'")
    model_name: str = Field("gpt-6-astra", description="Model ismi (örn: gpt-6-astra, gemini-1.5-flash)")

@router.post("/engine/ai-model")
async def set_ai_model(req: AiModelRequest):
    import os
    import dotenv
    from pathlib import Path
    try:
        # Bellekte güncelle
        os.environ["LLM_PROVIDER"] = req.provider
        os.environ["OPENAI_MODEL_NAME"] = req.model_name
        
        # Kalıcı olması için .env dosyasına yaz
        env_path = Path(".env")
        if not env_path.exists():
            env_path.touch()
            
        dotenv.set_key(str(env_path), "LLM_PROVIDER", req.provider)
        dotenv.set_key(str(env_path), "OPENAI_MODEL_NAME", req.model_name)
        
        return {
            "status": "success",
            "message": f"Yapay Zeka Motoru başarıyla güncellendi: {req.provider.upper()} ({req.model_name})",
            "provider": req.provider,
            "model_name": req.model_name
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}


@router.get("/market/regime")
async def get_market_regime():
    """
    Canli Piyasa Rejimi (MEGA_BULL / BULL / SIDEWAYS / BEAR / CRASH)
    Risk Modu x Rejim kombinasyonuyla olusan ticaret profili ve trailing parametrelerini dondurur.
    Dashboard icin her 30s'de cagirilir.
    """
    try:
        from services.engine.market_regime_engine import regime_engine
        from services.market_feed.live_stream import live_trade_manager
        from core.config import settings
        import time

        # 60 saniyeden eskiyse yeniden hesapla
        if time.time() - regime_engine._last_update > 60:
            regime_engine.compute_regime(live_trade_manager.market_prices)

        display = regime_engine.get_regime_display()
        current_mode = settings.current_risk_mode

        # Her piyasa icin aktif ticaret profilini de ekle
        profiles = {}
        for market in ["CRYPTO", "NASDAQ", "BIST"]:
            try:
                profiles[market] = regime_engine.get_trade_profile(current_mode, market)
            except Exception:
                pass

        return {
            "status": "success",
            "current_risk_mode": current_mode,
            "regimes": display,
            "trade_profiles": profiles,
            "last_updated": regime_engine._last_update
        }
    except Exception as e:
        import traceback
        return {"status": "error", "message": str(e), "trace": traceback.format_exc()}
