from fastapi import APIRouter
from services.ranking.top20_engine import top20_engine, Top20EvaluationResponse
from services.indicators_engine.twelve_indicators import twelve_indicators_engine, TwelveIndicatorsData, TwelveIndicatorsScore
from services.risk_engine.margin_controller import margin_controller, MarginCalculationRequest, AsymmetricMarginPlan
from services.indicators_engine.quantitative_indicators import quantitative_engine_24, Quantitative24Data

router = APIRouter()

@router.get("/top20-recommendations", response_model=Top20EvaluationResponse)
async def get_top20_stock_recommendations():
    """
    12 İndikatör (%40), Haber Akışı (%20), Ülke Makro Trendi (%20) ve 
    Son 6 Aylık Analizör (%20) Sonuçlarına Göre Sıralanmış İlk 20 Hisse Öneri Listesi
    """
    return top20_engine.generate_top_20_recommendations()

@router.post("/evaluate-12-indicators", response_model=TwelveIndicatorsScore)
async def evaluate_twelve_indicators(data: TwelveIndicatorsData):
    """
    TradingView Geçerli 12 İndikatör Mantıksal Puanlama ve Sinyal Uç Noktası
    """
    return twelve_indicators_engine.evaluate(data)

@router.post("/calculate-asymmetric-margin", response_model=AsymmetricMarginPlan)
async def calculate_asymmetric_margin(req: MarginCalculationRequest):
    """
    +%1.0 Kâr Al / -%0.4 Zarar Kes (2.5:1 R:R) Asimetrik Marj ve Risksiz Pozisyon Boyutu Hesaplayıcı
    """
    return margin_controller.calculate_plan(req)

@router.get("/quantitative/top-suite")
async def get_quantitative_top_suite():
    """
    24 Matematiksel & Kantitatif İndikatörle Çok Kriterli Algoritmik Değerlendirme
    """
    universe = [
        {"symbol": "NVDA", "name": "NVIDIA Corporation", "price": 218.76, "rsi": 62.4, "macd_hist": 2.6, "z_score": 1.45, "hurst": 0.68, "er": 0.82, "cmo": 34.0, "r2": 0.89},
        {"symbol": "TSLA", "name": "Tesla Inc.", "price": 358.79, "rsi": 58.0, "macd_hist": 1.8, "z_score": 1.10, "hurst": 0.62, "er": 0.75, "cmo": 26.0, "r2": 0.81},
        {"symbol": "QQQ", "name": "Invesco QQQ (NASDAQ-100)", "price": 482.50, "rsi": 55.2, "macd_hist": 1.4, "z_score": 0.85, "hurst": 0.59, "er": 0.70, "cmo": 22.0, "r2": 0.78},
        {"symbol": "AAPL", "name": "Apple Inc.", "price": 224.20, "rsi": 54.0, "macd_hist": 1.1, "z_score": 0.72, "hurst": 0.58, "er": 0.68, "cmo": 20.0, "r2": 0.76},
        {"symbol": "MSFT", "name": "Microsoft Corporation", "price": 448.50, "rsi": 56.1, "macd_hist": 1.5, "z_score": 0.95, "hurst": 0.64, "er": 0.73, "cmo": 24.5, "r2": 0.82},
        {"symbol": "META", "name": "Meta Platforms Inc.", "price": 514.00, "rsi": 59.5, "macd_hist": 2.1, "z_score": 1.30, "hurst": 0.66, "er": 0.79, "cmo": 31.0, "r2": 0.86},
        {"symbol": "BTCUSDT", "name": "Bitcoin / Tether", "price": 65420.0, "rsi": 57.5, "macd_hist": 3.2, "z_score": 1.20, "hurst": 0.65, "er": 0.77, "cmo": 29.0, "r2": 0.84}
    ]

    results = []
    for item in universe:
        data = Quantitative24Data(
            rsi=item["rsi"],
            macd_hist=item["macd_hist"],
            z_score=item["z_score"],
            hurst_exponent=item["hurst"],
            kama_efficiency_ratio=item["er"],
            cmo=item["cmo"],
            linear_regression_r2=item["r2"]
        )
        report = quantitative_engine_24.evaluate(data)
        results.append({
            "symbol": item["symbol"],
            "name": item["name"],
            "price": item["price"],
            "report": report
        })

    return {
        "status": "success",
        "total_indicators_suite": 24,
        "results": results
    }
