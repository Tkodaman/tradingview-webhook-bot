import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
import sys
import os
import asyncio
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(override=True)

# Proje kök dizinini sys.path'e ekle
BASE_DIR_PATH = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR_PATH not in sys.path:
    sys.path.insert(0, BASE_DIR_PATH)

from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from core.config import settings
from core.logger import logger
from services.engine.auto_runner import tv_auto_runner
from services.engine.scheduler import start_scheduler
from services.trainer.bot_trainer import bot_trainer

# Routers
from routers.webhook_router import router as webhook_router
from routers.websocket_router import router as websocket_router, live_data_broadcaster
from routers.agent_router import router as agent_router
from routers.market_router import router as market_router
from routers.position_router import router as position_router
from routers.engine_router import router as engine_router
from routers.memory_router import router as memory_router
from routers.intelligence_router import router as intelligence_router
from routers.indicators_router import router as indicators_router
from routers.profit_advisor_router import router as profit_advisor_router
from routers.ide_router import router as ide_router
from routers.analytics_router import router as analytics_router
from services.market_feed.live_stream import LiveTradeManager

async def start_shadow_scanner():
    """
    Kullanıcının belirlediği Watchlist'i her 6 dakikada bir tarayıp 
    Pre-Cognitive Shadow AI Cache'ini yeniler.
    """
    from services.analyzer.agent import analyzer_agent
    from schemas.webhook import WebhookSignal
    from services.ai_agent.research_engine import financial_agent
    from services.data_ingestion.tradingview_live_client import tradingview_live_client
    
    WATCHLIST = ["BTCUSD", "ETHUSD", "TSLA", "NVDA", "QQQ"]
    
    while True:
        try:
            logger.info("[SHADOW SCANNER] Pre-Cognitive yapay zeka ön belleği güncelleniyor...")
            live_data = await asyncio.to_thread(tradingview_live_client.fetch_live_market_data)
            for symbol in WATCHLIST:
                market_item = live_data.get(symbol)
                if not market_item or float(market_item.get("price", 0.0) or 0.0) <= 0:
                    logger.info(f"[SHADOW AI] {symbol} için doğrulanmış fiyat yok; cache yazılmadı.")
                    continue

                mock_signal = WebhookSignal(
                    symbol=symbol,
                    action="BUY", 
                    price=float(market_item["price"]),
                    quantity=1.0,
                    passphrase=settings.passphrase,
                    timeframe="15m",
                    indicators={
                        key: value for key, value in market_item.items()
                        if key in {"rsi", "macd", "atr_pct", "adx", "volume_ratio", "cmf"}
                        and isinstance(value, (int, float))
                    }
                )
                try:
                    audit_result = await asyncio.to_thread(
                        financial_agent.audit_tradingview_signal_concurrently,
                        mock_signal
                    )
                    
                    # Cache'e yaz
                    analyzer_agent.shadow_analysis_cache[symbol] = {
                        "skills_audit": audit_result,
                        "agent_verdict": "PRE_COGNITIVE_READY",
                        "_timestamp": time.time()
                    }
                    logger.info(f"🔮 [SHADOW AI] {symbol} gölge analizi tamamlandı (Skor: {audit_result.get('overall_skill_score', 0)}).")
                except Exception as e:
                    logger.warning(f"⚠️ [SHADOW AI] {symbol} güncellenirken hata: {e}")
                
                # API limitlerini zorlamamak için semboller arası 10 sn bekle
                await asyncio.sleep(10)
                
        except Exception as e:
            logger.error(f"[SHADOW SCANNER] Döngü hatası: {e}")
            
        # 6 dakika (360 saniye) bekle
        await asyncio.sleep(360)

app = FastAPI(title="TradingView AI Webhook Gateway, Risk Engine & 10-Skill Financial AI Analyst")

from services.market_feed.live_stream import live_trade_manager
@app.on_event("startup")
async def startup_event():
    logger.info("[STARTUP] Başlatılıyor: 7/24 Kesintisiz Otonom Strateji Motoru Arka Planda Aktif Edildi.")
    asyncio.create_task(tv_auto_runner.start_continuous_background_loop())
    
    # Shadow AI (Gölge Zeka) Cache Tarayıcısını Başlat
    asyncio.create_task(start_shadow_scanner())
    
    # Start WebSocket Broadcaster
    asyncio.create_task(live_data_broadcaster(live_trade_manager))
    
    # Start Alpaca Trade Updates WebSocket (Zero-latency Close detection)
    try:
        from services.broker.alpaca_stream import start_alpaca_stream
        asyncio.create_task(start_alpaca_stream())
        logger.info("[STARTUP] Alpaca WS Trade Updates (Sıfır Gecikme) Dinleyicisi Başlatıldı.")
    except Exception as e:
        logger.error(f"[STARTUP] Alpaca WS Başlatılamadı: {e}")

    # Start Alpaca Market Data WebSocket (Real-time Prices & Dynamic AI SL/TP)
    try:
        from services.broker.alpaca_data_stream import start_alpaca_data_stream
        asyncio.create_task(start_alpaca_data_stream())
        logger.info("[STARTUP] Alpaca Data Stream (Canlı Fiyat & Dinamik Makas) Dinleyicisi Başlatıldı.")
    except Exception as e:
        logger.error(f"[STARTUP] Alpaca Data Stream Başlatılamadı: {e}")

    # Scheduler (BIST ve NASDAQ Zamanlanmış Görevleri)
    start_scheduler()

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

# Static dosyalar (logo, resimler) için
images_dir = BASE_DIR / "static" / "images"
images_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

# Kodaman logo base64 - statik dosya yolu sorununu tamamen ortadan kaldirir
import base64
_LOGO_B64 = ""
try:
    _logo_path = BASE_DIR / "static" / "images" / "kodaman_logo.png"
    if _logo_path.exists():
        _LOGO_B64 = "data:image/png;base64," + base64.b64encode(_logo_path.read_bytes()).decode()
except Exception:
    pass

# Kodaman logo2 (gumus/gri - sag ust kose icin)
_LOGO2_B64 = ""
try:
    _logo2_path = BASE_DIR / "static" / "images" / "kodaman_logo2.png"
    if _logo2_path.exists():
        _LOGO2_B64 = "data:image/png;base64," + base64.b64encode(_logo2_path.read_bytes()).decode()
except Exception:
    pass

@app.get("/", response_class=HTMLResponse)
async def get_dashboard(request: Request):
    """
    Gerçek zamanlı web kokpiti, risk analiz göstergesi ve 10-Skill AI Analist Hub.
    """
    return templates.TemplateResponse(
        request=request,
        name="dashboard.html",
        context={
            "trading_mode": settings.trading_mode,
            "settings": settings,
            "trainer_params": bot_trainer.best_params,
            "kodaman_logo_b64": _LOGO_B64,
            "kodaman_logo2_b64": _LOGO2_B64,
            "llm_provider": os.getenv("LLM_PROVIDER", "openai").lower(),
            "openai_model_name": os.getenv("OPENAI_MODEL_NAME", "gpt-6-astra").lower()
        }
    )

@app.post("/api/train")
async def trigger_bot_training(iterations: int = 200):
    """
    Piyasa senaryoları üzerinde modeli eğitir ve optimum ağırlıkları kalibre eder
    """
    training_summary = bot_trainer.train_bot(iterations=iterations)
    return JSONResponse(content=training_summary)

class TradeLifecycleRequest(BaseModel):
    capital_usd: float = Field(100.0, description="Kullanılacak Örnek Sermaye ($ / ₺)")
    symbol: str = Field("NVDA", description="İşlem Yapılacak Hisse/Varlık")
    market: str = Field("NASDAQ", description="NASDAQ veya BIST")
    entry_price: float = Field(128.50, description="Hisse Giriş Fiyatı")
    target_profit_pct: float = Field(3.50, description="Kâr Al Yüzdesi (%)")
    stop_loss_pct: float = Field(1.75, description="Zarar Kes Yüzdesi (%)")
    slippage_pct: float = Field(0.08, description="Kayma Payı (%)")

@app.post("/api/simulate-trade-lifecycle")
async def simulate_trade_lifecycle(req: TradeLifecycleRequest):
    """
    100$ (veya belirlenen bütçe) ile TradingView Eş Zamanlı Sinyal, Giriş-Çıkış,
    Başa Baş (Break-Even) ve Net Bilanço Yaşam Döngüsü Simülatörü
    """
    from services.risk_engine.margin_controller import margin_controller, MarginCalculationRequest
    plan = margin_controller.calculate_plan(MarginCalculationRequest(
        account_size=req.capital_usd,
        risk_per_trade_pct=req.stop_loss_pct,
        entry_price=req.entry_price,
        symbol=req.symbol,
        market=req.market,
        action="BUY",
        target_profit_pct=req.target_profit_pct,
        stop_loss_pct=req.stop_loss_pct,
        slippage_rate_pct=req.slippage_pct,
        max_position_margin_pct=100.0  # 100$ tam alım simülasyonu
    ))

    shares = round(req.capital_usd / req.entry_price, 4)
    gross_gain = round(shares * (plan.target_profit_price - req.entry_price), 2)
    costs = plan.cost_breakdown_at_target
    net_gain = round(gross_gain - costs.total_friction_costs, 2)
    final_balance = round(req.capital_usd + net_gain, 2)
    currency = plan.currency

    steps = [
        {
            "step_number": 1,
            "stage": "📡 1. Sinyal Tespiti & 12 İndikatör Doğrulaması",
            "status": "APPROVED",
            "description": f"TradingView webhook sinyali eş zamanlı yakalandı. {req.symbol} için 12 İndikatör Skoru %92 onay verdi (RSI: 58.2, SuperTrend: Boğa, VWAP üstü).",
            "metrics": {
                "Sinyal Fiyatı": f"{currency}{req.entry_price:.2f}",
                "Ayrılan Bütçe": f"{currency}{req.capital_usd:.2f}",
                "Hesaplanan Lot/Adet": f"{shares} Lot"
            }
        },
        {
            "step_number": 2,
            "stage": "⚡ 2. Pozisyon Açılışı & Kayma (Slippage) Girişi",
            "status": "EXECUTED",
            "description": f"%{req.slippage_pct:.2f} kayma payı hesaba katılarak gerçek piyasa eşleşmesi {currency}{plan.slippage_adjusted_entry_price:.2f} üzerinden yapıldı.",
            "metrics": {
                "Gerçek Giriş": f"{currency}{plan.slippage_adjusted_entry_price:.2f}",
                "İlk Stop-Loss (-%{req.stop_loss_pct:.2f})": f"{currency}{plan.stop_loss_price:.2f}",
                "Alış Komisyonu": f"{currency}{costs.buy_commission:.2f}"
            }
        },
        {
            "step_number": 3,
            "stage": "🔒 3. Fiyat İlerlemesi & Başa Baş (Break-Even) Kilitleme",
            "status": "RISK_FREE_TRIGGERED",
            "description": f"Fiyat +%1.20 kâra ({currency}{plan.break_even_trigger_price:.2f}) ulaştığında Trailing Stop devreye girdi ve stop seviyesi {currency}{plan.break_even_guaranteed_stop_price:.2f} seviyesine taşındı. İşlem %100 risksiz (Free-Roll) hale geldi.",
            "metrics": {
                "Tetikleme Fiyatı": f"{currency}{plan.break_even_trigger_price:.2f}",
                "Garantili Stop": f"{currency}{plan.break_even_guaranteed_stop_price:.2f}",
                "Kalan Risk": f"{currency}0.00 (Sıfır Risk)"
            }
        },
        {
            "step_number": 4,
            "stage": "🏆 4. Hedefe Ulaşma & Net Kâr Realizasyonu",
            "status": "TAKE_PROFIT_HIT",
            "description": f"Fiyat +%{req.target_profit_pct:.2f} hedef fiyatına ({currency}{plan.target_profit_price:.2f}) ulaştı ve kâr realize edildi.",
            "metrics": {
                "Çıkış Fiyatı": f"{currency}{plan.target_profit_price:.2f}",
                "Brüt Kâr": f"+{currency}{gross_gain:.2f}",
                "Toplam Komisyon & Slippage": f"-{currency}{costs.total_friction_costs:.2f}",
                "Net Ele Geçen Kâr": f"+{currency}{net_gain:.2f} (Net %{costs.net_roi_pct:.2f})",
                "Yeni Kasa Bakiyesi": f"{currency}{final_balance:.2f}"
            }
        }
    ]

    return {
        "title": f"${req.capital_usd:.0f} {req.symbol} Canlı İşlem Yaşam Döngüsü Simülasyonu",
        "symbol": req.symbol,
        "market": req.market,
        "initial_capital": req.capital_usd,
        "final_capital": final_balance,
        "net_profit": net_gain,
        "net_roi_pct": costs.net_roi_pct,
        "currency": currency,
        "risk_reward_ratio": plan.risk_reward_ratio,
        "lifecycle_steps": steps
    }


# Register Routers
app.include_router(webhook_router)
app.include_router(websocket_router)
app.include_router(agent_router, prefix="/api/agent")
app.include_router(market_router, prefix="/api/market")
app.include_router(position_router, prefix="/api/positions")
app.include_router(engine_router, prefix="/api")
app.include_router(memory_router, prefix="/api/experience-memory")
app.include_router(intelligence_router, prefix="/api/llm-intelligence")
app.include_router(indicators_router, prefix="/api/indicators")
app.include_router(profit_advisor_router, prefix="/api/profit-advisor")
app.include_router(ide_router, prefix="/api/ide")
app.include_router(analytics_router, prefix="/api/analytics")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
