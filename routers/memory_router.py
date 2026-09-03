import io
import csv
from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from services.engine.experience_memory_engine import experience_memory_engine
from services.engine.autonomous_tracker import journey_tracker
from services.engine.trade_journal_learning import trade_journal_engine

router = APIRouter()

@router.get("/summary")
async def get_experience_memory_summary():
    """
    Otonom İç Deneyim & Dinamik Tecrübe Hafızası Sentezi
    """
    return {
        "status": "success",
        "data": experience_memory_engine.get_summary()
    }

@router.get("/algorithmic-stats")
async def get_algorithmic_stats():
    """
    Algoritmik Hata Payı Eğrisi ve Geleceğe Dair Eylem Planı (Kazan-Kazan)
    """
    return {
        "status": "success",
        "data": experience_memory_engine.get_algorithmic_statistics()
    }

@router.get("/timeline")
async def get_autonomous_tracker_timeline():
    """
    Otonom Sürüş Yol Haritası & Saatlik / 8 Saatlik İlerleme Takipçisi
    """
    return journey_tracker.get_timeline_data()

@router.get("/asset-confidence-index")
async def get_asset_confidence_index():
    """
    Geçmiş Arşiv İstatistiklerinden Türetilen Algoritmik Hisse/Varlık Güven Endeksi & Dinamik Uzmanlık Sıralaması
    """
    rankings = experience_memory_engine.get_asset_confidence_index()
    return {
        "status": "success",
        "total_assets_ranked": len(rankings),
        "rankings": rankings
    }

@router.get("/trades")
async def get_experience_trades():
    """
    Detaylı Trade Post-Mortem ve Çıkarılan Dersler Listesi
    """
    return {
        "status": "success",
        "trade_count": len(experience_memory_engine.trade_history),
        "trades": experience_memory_engine.trade_history
    }

@router.get("/export/json")
async def export_experience_json():
    """Tarihsel deneyim verilerini JSON formatında dışa aktar"""
    return experience_memory_engine.get_summary().model_dump()

@router.get("/export/csv")
async def export_experience_csv():
    """Tarihsel işlemleri CSV formatında dışa aktar"""
    trades = experience_memory_engine.trade_history
    output = io.StringIO()
    writer = csv.writer(output)
    
    if trades:
        headers = list(trades[0].model_dump().keys())
        writer.writerow(headers)
        for trade in trades:
            row = []
            for val in trade.model_dump().values():
                if isinstance(val, dict):
                    row.append(str(val))
                else:
                    row.append(val)
            writer.writerow(row)
            
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=experience_history.csv"}
    )

class SimulateTradeMemoryRequest(BaseModel):
    symbol: str = Field("NVDA", description="İşlem sembolü")
    action: str = Field("BUY", description="Yön")
    entry_price: float = Field(220.0, description="Giriş fiyatı")
    exit_price: float = Field(225.5, description="Çıkış fiyatı")
    pnl_pct: float = Field(2.5, description="PnL Yüzdesi (%)")
    market_regime: str = Field("GÜÇLÜ KANTİTATİF BOĞA", description="Piyasa rejimi")

@router.post("/simulate-trade")
async def simulate_experience_trade(req: SimulateTradeMemoryRequest):
    """
    Otonom Tecrübe Hafızasına test işlemi enjekte eder ve anlık kuralları yeniden kalibre eder
    """
    trade = experience_memory_engine.record_completed_trade(
        symbol=req.symbol,
        action=req.action,
        entry_price=req.entry_price,
        exit_price=req.exit_price,
        pnl_pct=req.pnl_pct,
        market_regime=req.market_regime,
        indicators={"rsi": 62, "volume_ratio": 1.6, "atr_pct": 1.8}
    )
    return {
        "status": "success",
        "trade": trade.model_dump(),
        "summary": experience_memory_engine.get_summary().model_dump()
    }

@router.post("/calibrate")
async def calibrate_experience_memory():
    """
    Hafıza motorunu ve dinamik çarpanları yeniden kalibre eder
    """
    experience_memory_engine._derive_synthesized_insights()
    summary = experience_memory_engine.get_summary()
    return {
        "status": "success",
        "message": "Dinamik Tecrübe Hafızası başarıyla yeniden kalibre edildi.",
        "multiplier": summary.dynamic_experience_multiplier,
        "rules_count": len(summary.learned_rules_and_insights),
        "total_trades": summary.total_trades_analyzed,
        "win_rate": summary.win_rate_historical
    }

class LogInjectRequest(BaseModel):
    market: str = Field("NASDAQ", description="BIST veya NASDAQ")
    level: str = Field("INFO", description="INFO, SCAN, ORDER, WIN, WARN")
    message: str = Field("Otonom sinyal taraması tamamlandı.", description="Mesaj")

@router.post("/test-log")
async def inject_experience_log(req: LogInjectRequest):
    """
    Canlı terminallere anlık log enjekte eder
    """
    experience_memory_engine.add_live_log(req.market, req.level, req.message)
    return {"status": "success", "market": req.market, "level": req.level, "message": req.message}

@router.get("/journal")
async def get_trade_journal_learning():
    """
    Sert Giriş/Çıkış Eğitimi, İşlem Günlüğü ve Birikim Veri Deposu
    """
    return trade_journal_engine.get_journal_summary()
