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
async def get_expectancy():
    """
    Gerçek işlem geçmişinden Expectancy (Beklenen Değer) ve Kelly Fraction hesaplar.
    """
    return expert_analytics_engine.get_expectancy_kelly(live_trade_manager.trade_history)


@router.get("/correlation")
async def get_correlation():
    """
    Açık pozisyonların anlık fiyatlarından biriken zaman serisiyle korelasyon ısı haritası üretir.
    """
    return expert_analytics_engine.get_correlation_heatmap(live_trade_manager.positions)


@router.get("/strategy-map")
async def get_strategy_map():
    """
    Piyasa Rejimi Tespit Motoru'nun son ürettiği sonuçlardan sembol -> strateji haritası.
    Aktif Risk & Frekans Modu'nun her sembole otonom uyguladığı canlı TP/SL dahildir.
    """
    from core.config import settings
    return {
        "current_risk_mode": settings.current_risk_mode,
        "strategies": expert_analytics_engine.get_strategy_map(market_regime_detector.last_results),
    }


@router.get("/thought-stream")
async def get_thought_stream():
    """
    Fakeout Guard, Stop-Hunt Evader ve Korelasyon Filtresi'nin canlı "neden bekliyorum/koruyorum" akışı.
    """
    return {"thoughts": bot_thought_stream.get_recent(30)}
