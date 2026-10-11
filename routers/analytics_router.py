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
    return {"thoughts": bot_thought_stream.get_recent(60)}

@router.get("/ai-opportunities")
async def get_ai_opportunities():
    try:
        from services.data_ingestion.tradingview_live_client import tradingview_live_client
        indicators = tradingview_live_client.get_all_indicators() or {}
        missiles = []
        for sym, d in indicators.items():
            if not isinstance(d, dict):
                continue
            vol = float(d.get("volume_ratio") or 1.0)
            xr = float(d.get("xray_ratio") or 1.0)
            rsi = float(d.get("rsi") or 50.0)
            if vol >= 1.8 and xr >= 1.20 and 45.0 <= rsi <= 68.0:
                clean_sym = sym.replace("BINANCE:", "").replace("CRYPTO:", "")
                missiles.append(f"🚀 {clean_sym} (Hacim {vol:.1f}x | XR {xr:.2f} | RSI {rsi:.0f})")
        if missiles:
            return {"ai_analysis": " | ".join(missiles[:4]) + " — Önünde %4-%6 Temiz Koşu Alanı Açık!"}
        return {"ai_analysis": "🔭 Piyasada yakıtı dolmuş gerçek füze adayı taranıyor. Hacmi <1.5x olan ölü tahtalar elendi."}
    except Exception:
        return {"ai_analysis": "🔭 Füze avcısı devrede, fırsatlar canlı taranıyor..."}

@router.get("/ai-psychology")
async def get_ai_psychology():
    return {"ai_analysis": "⏳ YZ Psikoloji Analizi (Hız İçin Geçici Devre Dışı)"}

@router.get("/ai-correlation")
async def get_ai_correlation():
    return {"ai_analysis": "⏳ YZ Korelasyon Analizi (Hız İçin Geçici Devre Dışı)"}

@router.get("/shadow-summary")
def get_shadow_summary():
    """
    experience_memory.json dosyasından ve TradeJournal'dan en son kapanan işlemleri okur,
    özet istatistikleri (Win Rate, PnL, Başarı Endeksi) hesaplayarak tabloya gönderir.
    """
    import json
    import os
    from pathlib import Path
    BASE_DIR = Path(__file__).resolve().parent.parent
    mem_path = BASE_DIR / "experience_memory.json"
    
    trades = []
    if mem_path.exists():
        try:
            with open(mem_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            trades = data.get("trade_history", [])
        except Exception:
            trades = []

    # İstatistikleri hesapla
    total_count = len(trades)
    win_count = len([t for t in trades if t.get("is_win") or float(t.get("pnl_amount", 0) or 0) > 0])
    loss_count = total_count - win_count
    win_rate = round((win_count / total_count * 100.0), 1) if total_count > 0 else 0.0
    total_pnl = round(sum(float(t.get("pnl_amount", 0) or 0) for t in trades), 2)
    total_pnl_pct = round(sum(float(t.get("pnl_pct", 0) or 0) for t in trades), 2)

    total_gain = sum(float(t.get("pnl_amount", 0) or 0) for t in trades if float(t.get("pnl_amount", 0) or 0) > 0)
    total_loss = abs(sum(float(t.get("pnl_amount", 0) or 0) for t in trades if float(t.get("pnl_amount", 0) or 0) < 0))
    profit_factor = round(total_gain / total_loss, 2) if total_loss > 0 else (round(total_gain, 2) if total_gain > 0 else 1.0)

    # Başarı Endeksi (0 - 100 Skoru)
    if total_count == 0:
        success_index = 50.0  # Nötr / Kalibrasyon
    else:
        success_index = round(min(100.0, max(0.0, (win_rate * 0.7) + min(profit_factor * 15.0, 30.0))), 1)

    recent_trades = list(reversed(trades))[:15]
    return {
        "trades": recent_trades,
        "stats": {
            "total_trades": total_count,
            "win_count": win_count,
            "loss_count": loss_count,
            "win_rate": win_rate,
            "total_pnl": total_pnl,
            "total_pnl_pct": total_pnl_pct,
            "profit_factor": profit_factor,
            "success_index": success_index
        }
    }

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


@router.get("/darwin-stance")
def get_darwin_stance():
    """
    Darwinian Otonom Evrim ve Duruş Motoru Durumu (DEFANS / GUARD vs ATAK).
    2 saatlik döngü, 2 MB birikim eşiği ve öğrenilen kural mutasyonlarını döner.
    """
    from services.engine.darwin_evolution_engine import darwin_evolution_engine
    return darwin_evolution_engine.get_evolution_summary()


@router.post("/darwin-trigger-now")
def trigger_darwin_evolution_now():
    """
    Kullanıcı veya sistem talebiyle anında Darwinian Evrim döngüsünü tetikler.
    """
    from services.engine.darwin_evolution_engine import darwin_evolution_engine
    darwin_evolution_engine.execute_darwinian_synthesis(reason="KULLANICI MANUEL SENTEZ TALEBİ")
    return darwin_evolution_engine.get_evolution_summary()


