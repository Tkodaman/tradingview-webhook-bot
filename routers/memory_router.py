import io
import csv
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from services.engine.experience_memory_engine import experience_memory_engine
from services.engine.autonomous_tracker import journey_tracker
from services.engine.trade_journal_learning import trade_journal_engine

router = APIRouter()

import json
import os

@router.get("/summary")
def get_experience_memory_summary():
    """
    Otonom İç Deneyim & Dinamik Tecrübe Hafızası Sentezi
    """
    data = experience_memory_engine.get_summary().model_dump()
    
    # Portföyü frontend'e taşıyalım
    portfolio_path = os.path.join(os.getcwd(), "portfolio_memory.json")
    active_portfolio = []
    if os.path.exists(portfolio_path):
        try:
            with open(portfolio_path, "r", encoding="utf-8") as f:
                p_data = json.load(f)
                active_portfolio = p_data.get("crypto_portfolio", {}).get("assets", [])
        except Exception:
            pass
            
    data["active_portfolio"] = active_portfolio

    return {
        "status": "success",
        "data": data
    }

@router.get("/algorithmic-stats")
def get_algorithmic_stats():
    """
    Algoritmik Hata Payı Eğrisi ve Geleceğe Dair Eylem Planı (Kazan-Kazan)
    """
    return {
        "status": "success",
        "data": experience_memory_engine.get_algorithmic_statistics()
    }

@router.get("/timeline")
def get_autonomous_tracker_timeline():
    """
    Otonom Sürüş Yol Haritası & Saatlik / 8 Saatlik İlerleme Takipçisi
    """
    return journey_tracker.get_timeline_data()

@router.get("/asset-confidence-index")
def get_asset_confidence_index():
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
def get_experience_trades():
    """
    Detaylı Trade Post-Mortem ve Çıkarılan Dersler Listesi
    """
    return {
        "status": "success",
        "trade_count": len(experience_memory_engine.trade_history),
        "trades": experience_memory_engine.trade_history
    }

@router.get("/advanced-metrics")
def get_advanced_metrics():
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
def export_experience_json():
    """Tarihsel deneyim verilerini JSON formatında dışa aktar"""
    return experience_memory_engine.get_summary().model_dump()

@router.get("/dynamic-voice")
def get_dynamic_voice():
    """LLM tarafindan uretilen dis ses ve alarm metinlerini dondurur"""
    from services.engine.voice_engine import ai_voice_engine
    return {
        "status": "success",
        "alarm": ai_voice_engine.current_alarm,
        "thought": ai_voice_engine.current_thought,
        "last_update": ai_voice_engine.last_update.strftime("%H:%M:%S")
    }

@router.get("/export/csv")
def export_experience_csv():
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
def simulate_experience_trade(req: SimulateTradeMemoryRequest):
    """
    Otonom Tecrübe Hafızasına test işlemi enjekte eder ve anlık kuralları yeniden kalibre eder
    """
    raise HTTPException(status_code=410, detail="Sentetik işlemlerin işlem hafızasına yazılması kapatıldı.")

@router.post("/calibrate")
def calibrate_experience_memory():
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
def inject_experience_log(req: LogInjectRequest):
    """
    Canlı terminallere anlık log enjekte eder
    """
    raise HTTPException(status_code=410, detail="Canlı günlüklere dışarıdan test mesajı eklenmesi kapatıldı.")

@router.get("/journal")
def get_trade_journal_learning():
    """
    Sert Giriş/Çıkış Eğitimi, İşlem Günlüğü ve Birikim Veri Deposu
    """
    return trade_journal_engine.get_journal_summary()

@router.get("/learning-curve")
def get_learning_curve():
    """
    Geçmişteki gerçek işlemlere dayanarak Otonom Makine Öğrenmesi (ML) gelişim eğrisini oluşturur.
    Gerçek kümülatif win_rate ve kümülatif profit factor hesaplanır.
    """
    from services.engine.learning_curve import build_learning_curve
    return build_learning_curve(experience_memory_engine.trade_history)
