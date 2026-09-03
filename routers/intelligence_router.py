from fastapi import APIRouter
from fastapi.responses import JSONResponse
from services.intelligence.llm_market_intelligence import llm_market_intelligence
from services.engine.advanced_analytics import advanced_analytics_engine

router = APIRouter()

@router.get("/summary")
async def get_llm_intelligence_summary():
    """
    LLM Çok Kaynaklı Piyasa İstihbaratı (FinTwit, Bloomberg, KAP Bildirimleri, Şirket Bilançoları)
    """
    return llm_market_intelligence.generate_comprehensive_intelligence_summary()

@router.get("/earnings/{symbol}")
async def get_stock_earnings_breakdown(symbol: str):
    """
    Hisse Başına Çeyreklik Bilanço ve Kâr/Zarar Çözümleyicisi
    """
    return llm_market_intelligence.get_financial_earnings_breakdown(symbol.upper())

@router.get("/kap")
async def get_live_kap_disclosures():
    """
    Canlı KAP (Kamuyu Aydınlatma Platformu) Bildirimleri
    """
    return {
        "status": "success",
        "disclosures": llm_market_intelligence.get_kap_disclosures()
    }

@router.get("/advanced/scan")
async def get_advanced_analytics_scan():
    """
    Birleştirilmiş Makine Öğrenimi ve Niteliksel Evren Taraması
    """
    return {
        "status": "success",
        "target_sharpe_threshold": advanced_analytics_engine.target_sharpe_threshold,
        "scanned_universe": advanced_analytics_engine.scan_active_universe()
    }

@router.get("/advanced/evaluate/{symbol}")
async def evaluate_advanced_symbol(symbol: str):
    """
    Tek Hisse İçin Birleşik XGBoost & Bayesyen Sharpe Oranı Analizi
    """
    return advanced_analytics_engine.evaluate_symbol(symbol=symbol.upper(), price=100.0)

@router.get("/advanced/seasonal-evaluation")
async def get_seasonal_evaluation():
    """Son sezonluk/dönemsel LLM değerlendirmesini (Evaluation Bubble) döner."""
    return JSONResponse(content=advanced_analytics_engine.get_seasonal_evaluation())
