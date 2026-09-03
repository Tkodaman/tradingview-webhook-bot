"""
Profit Advisor Router — /api/profit-advisor
============================================
Botun iç dünyasını analiz eden ProfitAdvisorAgent'ın sonuçlarını
sunan API endpoint'leri.
"""

from fastapi import APIRouter
from core.logger import logger

router = APIRouter()


@router.get("/report")
async def get_profit_advisor_report():
    """
    Tam kâr analiz raporu:
    - Pariite optimizasyonu (hangi semboller kârlı/toksik?)
    - Strateji rotasyonu (MOMENTUM vs MEAN_REVERSION vs ARB)
    - Zaman penceresi (en iyi gün/saat)
    - Lot boyutu önerisi (kazanç serisinde artır, kayıp serisinde küçült)
    - Skill zayıflık raporu (hangi rejimler bloke edilmiş?)
    - Aksiyonel sonraki adımlar (öncelik sırası ile)
    """
    try:
        from services.agents.profit_advisor_agent import profit_advisor_agent
        report = profit_advisor_agent.generate_full_report()
        return report
    except Exception as e:
        logger.error(f"[PROFIT ADVISOR] Rapor hatası: {e}")
        return {"status": "error", "message": str(e)}


@router.get("/quick-verdict")
async def get_quick_verdict():
    """
    Hızlı özet: Win rate, net PnL, lot önerisi ve bir sonraki aksiyon.
    Dashboard widget'ı için optimize edilmiş hafif endpoint.
    """
    try:
        from services.agents.profit_advisor_agent import profit_advisor_agent
        from services.engine.experience_memory_engine import experience_memory_engine
        from services.market_feed.live_stream import live_trade_manager

        history = experience_memory_engine.trade_history
        open_pos = [p for p in live_trade_manager.positions.values() if p.status == "OPEN"]

        if not history:
            return {
                "status": "success",
                "win_rate_pct": 0,
                "net_pnl_usd": 0.0,
                "total_trades": 0,
                "open_positions": len(open_pos),
                "lot_action": "HOLD",
                "top_next_action": "Veri bekleniyor — ilk 10 işlem sonrası analiz hazır.",
                "verdict_emoji": "⏳",
            }

        wins = [t for t in history if t.is_win]
        net  = round(sum(t.pnl_amount for t in history), 2)
        wr   = round(len(wins) / len(history) * 100, 1)

        # Hızlı lot tavsiyesi
        last5 = history[-5:]
        recent_wins = sum(1 for t in last5 if t.is_win)
        if recent_wins >= 4:
            lot_action = "ARTIR 🟢"
        elif recent_wins <= 1:
            lot_action = "KÜÇÜLT 🔴"
        else:
            lot_action = "KORU 🟡"

        # Özet karar
        if wr >= 65 and net > 0:
            verdict = "🚀 KÂRLı & SAĞLIKLI"
        elif wr >= 50 and net > 0:
            verdict = "✅ KAZANÇ BÖLGESINDE"
        elif wr >= 40:
            verdict = "⚠️ İYİLEŞTİRME GEREKLİ"
        else:
            verdict = "🔴 ZARARDA — ACİL ÖNLEM"

        return {
            "status": "success",
            "win_rate_pct": wr,
            "net_pnl_usd": net,
            "total_trades": len(history),
            "open_positions": len(open_pos),
            "lot_action": lot_action,
            "verdict": verdict,
        }
    except Exception as e:
        logger.error(f"[PROFIT ADVISOR QUICK] Hata: {e}")
        return {"status": "error", "message": str(e)}
