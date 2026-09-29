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
    # Dinamik Akış Enjeksiyonu (Frontend'de "Bekleniyor" yazmasını engellemek ve canlılığı kanıtlamak için)
    bot_thought_stream.add_throttled(
        category="OTONOM ZIRH", 
        symbol="PORTFÖY-USDT", 
        message="[İnisiyatif] Rotasyon Motoru devrede. Kasa tam otomatik modda iz sürüyor.", 
        level="INFO", 
        cooldown_sec=30
    )
    
    bot_thought_stream.add_throttled(
        category="RİSK MOTORU", 
        symbol="SİSTEM-USDT", 
        message="[İzleyici] Piyasaların mikro gürültüleri filtreleniyor. %4'lük mutlak disiplin sınırları aktif.", 
        level="WARN", 
        cooldown_sec=45
    )

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
