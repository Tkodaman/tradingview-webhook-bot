"""
Uzman Analitik Uc Noktalari (Expert Analytics Endpoints)
Expectancy/Kelly, Korelasyon Isi Haritasi ve Strateji Router paneli icin veri sağlar.
"""
from fastapi import APIRouter, Depends
from core.security import verify_ip
from services.market_feed.live_stream import live_trade_manager
from services.intelligence.market_regime_detector import market_regime_detector
from services.risk_engine.expert_analytics import expert_analytics_engine
from services.engine.bot_thought_stream import bot_thought_stream

router = APIRouter(dependencies=[Depends(verify_ip)])


@router.get("/expectancy")
def get_expectancy():
    """
    Gerçek işlem geçmişinden Expectancy (Beklenen Değer) ve Kelly Fraction hesaplar.
    """
    return expert_analytics_engine.get_expectancy_kelly(live_trade_manager.trade_history)


@router.get("/correlation")
def get_correlation():
    """
    Açık pozisyonların anlık fiyatlarından biriken zaman serisiyle korelasyon ısı haritası üretir.
    """
    return expert_analytics_engine.get_correlation_heatmap(live_trade_manager.positions)


@router.get("/strategy-map")
def get_strategy_map():
    """
    Piyasa Rejimi Tespit Motoru'nun son ürettiği sonuçlardan strateji haritası.
    Aktif Risk & Frekans Modu'nun her sembole otonom uyguladığı canlı TP/SL dahildir.
    """
    from core.config import settings
    return {
        "current_risk_mode": settings.current_risk_mode,
        "strategies": expert_analytics_engine.get_strategy_map(),
    }


@router.get("/thought-stream")
def get_thought_stream():
    """
    Fakeout Guard, Stop-Hunt Evader ve Korelasyon Filtresi'nin canlı "neden bekliyorum/koruyorum" akışı.
    """
    return {"thoughts": bot_thought_stream.get_recent(30)}

@router.get("/ai-opportunities")
def get_ai_opportunities():
    """
    Top-5 Fırsat için LLM Avcı Sentezi
    """
    from services.ai.ai_dashboard_advisor import ai_dashboard_advisor
    return {"ai_analysis": ai_dashboard_advisor.get_opportunity_analysis()}

@router.get("/ai-psychology")
def get_ai_psychology():
    """
    Korku/Açgözlülük ve Makro Kalkan için LLM Psikoloji Sentezi
    """
    from services.ai.ai_dashboard_advisor import ai_dashboard_advisor
    return {"ai_analysis": ai_dashboard_advisor.get_psychology_synthesis()}

@router.get("/ai-correlation")
def get_ai_correlation():
    """
    Uzman Analitik: Açık Pozisyonların Otonom Double-Exposure Sentezi
    """
    from services.ai.ai_dashboard_advisor import ai_dashboard_advisor
    return {"ai_analysis": ai_dashboard_advisor.get_correlation_synthesis()}

@router.get("/shadow-summary")
def get_shadow_summary():
    """
    experience_memory.json dosyasından en son kapanan işlemleri okur ve tabloya gönderir.
    """
    import json
    import os
    from pathlib import Path
    BASE_DIR = Path(__file__).resolve().parent.parent
    mem_path = BASE_DIR / "experience_memory.json"
    
    if not mem_path.exists():
        return {"trades": []}
    try:
        with open(mem_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        trades = data.get("trade_history", [])
        # En yeni işlemler üstte olacak şekilde ters çevir ve son 15 işlemi al
        recent_trades = list(reversed(trades))[:15]
        return {"trades": recent_trades}
    except Exception as e:
        return {"trades": []}

@router.get("/shadow-active")
def get_shadow_active():
    """
    Canlı (Açık) Gölge Arena pozisyonlarını döndürür.
    """
    from services.market_feed.live_stream import live_trade_manager
    active_shadows = []
    for pos in live_trade_manager.shadow_positions.values():
        if pos.status == "OPEN":
            active_shadows.append(pos.model_dump())
    return {"active_shadows": active_shadows}

