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

@router.get("/advanced-metrics")
async def get_advanced_metrics():
    """
    5 adet yeni ML gelişmiş analitik grafiği (Radar, Donut, Scatter, Bar, Area)
    için gerekli olan veri setlerini döndürür.
    """
    metrics = experience_memory_engine.get_advanced_metrics()
    return {
        "status": "success",
        "data": metrics
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
    writer = csv.writer(output, delimiter=';', dialect='excel')
    
    # Kullanıcı dostu, Türkçe ve gruplandırılmış sütun başlıkları
    headers = [
        "Tarih/Saat",
        "İşlem ID",
        "Sembol",
        "Yön",
        "Giriş Fiyatı ($)",
        "Çıkış Fiyatı ($)",
        "Kâr/Zarar ($)",
        "Kâr/Zarar (%)",
        "İşlem Sonucu",
        "Süre (Dk)",
        "Kapanış Sebebi",
        "Piyasa Rejimi",
        "Maks. Drawdown (%)",
        "Giriş İndikatörleri",
        "Çıkarılan Ders",
        "Algoritmik Aksiyon Planı"
    ]
    writer.writerow(headers)
    
    for trade in trades:
        # İndikatörleri temiz metin formatına çevir
        inds = trade.indicators_at_entry
        inds_text = "Yok"
        if isinstance(inds, dict) and inds:
            inds_text = " | ".join([f"{str(k).upper()}: {v}" for k, v in inds.items()])
            
        row = [
            trade.timestamp,
            trade.trade_id,
            trade.symbol,
            trade.action,
            f"{trade.entry_price:.4f}",
            f"{trade.exit_price:.4f}",
            f"{trade.pnl_amount:.2f}",
            f"%{trade.pnl_pct:.2f}",
            "BAŞARILI" if trade.is_win else "ZARAR",
            str(trade.duration_minutes),
            trade.exit_reason,
            trade.market_regime,
            f"%{trade.max_drawdown_percent:.2f}",
            inds_text,
            trade.lesson_learned,
            trade.algorithmic_action_plan
        ]
        writer.writerow(row)
            
    # Türkçe karakter sorunu olmaması için BOM (Byte Order Mark) ekliyoruz
    csv_bytes = "\ufeff" + output.getvalue()
    
    return StreamingResponse(
        iter([csv_bytes.encode('utf-8')]),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": "attachment; filename=Trade_Gecmisi_Raporu.csv"}
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

@router.get("/learning-curve")
async def get_learning_curve():
    """
    Geçmişteki gerçek işlemlere dayanarak Otonom Makine Öğrenmesi (ML) gelişim eğrisini oluşturur.
    Gerçek kümülatif win_rate ve kümülatif profit factor hesaplanır.
    """
    from datetime import datetime
    
    trades = experience_memory_engine.trade_history
    if not trades:
        return {
            "status": "success",
            "learning_curve": [
                {
                    "date": datetime.now().strftime("%Y-%m-%d"),
                    "win_rate": 0.0,
                    "profit_factor": 0.0
                }
            ]
        }
        
    curve = []
    wins = 0
    total_gross_profit = 0.0
    total_gross_loss = 0.0
    
    cumulative_points = []
    for i, t in enumerate(trades):
        pnl = getattr(t, 'pnl_pct', 0.0)
        is_win = getattr(t, 'is_win', pnl > 0)
        
        if is_win:
            wins += 1
            total_gross_profit += pnl
        else:
            total_gross_loss += abs(pnl)
            
        current_win_rate = (wins / (i + 1)) * 100
        current_pf = total_gross_profit / total_gross_loss if total_gross_loss > 0 else (total_gross_profit if total_gross_profit > 0 else 0.0)
        
        cumulative_points.append({
            # Tarihin sadece gün kısmını al (ör: 2026-09-13)
            "date": getattr(t, 'timestamp', datetime.now().strftime("%Y-%m-%d"))[:10],
            "win_rate": round(current_win_rate, 1),
            "profit_factor": round(current_pf, 2)
        })
        
    # Eğer çok fazla işlem varsa grafiğin okunabilirliği için örneklem al (örn: 30 nokta)
    if len(cumulative_points) > 30:
        step = max(1, len(cumulative_points) // 30)
        curve = cumulative_points[::step]
        if curve[-1] != cumulative_points[-1]:
            curve.append(cumulative_points[-1])
    else:
        curve = cumulative_points
        
    return {
        "status": "success",
        "learning_curve": curve
    }
