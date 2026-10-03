import sys
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
import os

# Thread pool exhaustion (Özellikle Gemini 429 uyku (sleep) sürelerinde) sorununu çözmek için:
os.environ["ANYIO_MAX_THREADS"] = "200"

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
from routers.ai_chat_router import router as ai_chat_router

async def start_shadow_scanner():
    """
    Kullanıcının belirlediği Watchlist'i her 6 dakikada bir tarayıp 
    Pre-Cognitive Shadow AI Cache'ini yeniler.
    """
    from services.analyzer.agent import analyzer_agent
    from schemas.webhook import WebhookSignal
    from services.ai_agent.research_engine import financial_agent
    from services.data_ingestion.tradingview_live_client import tradingview_live_client
    
    from services.data_ingestion.asset_universe_manager import asset_universe_manager
    
    while True:
        try:
            logger.info("[SHADOW SCANNER] Pre-Cognitive yapay zeka ön belleği güncelleniyor...")
            
            # GÖLGE ARENA DİNAMİK VARLIK HAVUZU (Asset Universe Manager'dan anlık hedefler çekilir)
            active_targets = asset_universe_manager.get_active_tickers()
            
            # Borsaların öneklerini (BINANCE:, NASDAQ:) temizleyerek düz sembol listesi oluştur
            dynamic_watchlist = []
            for market_list in active_targets.values():
                for ticker in market_list:
                    clean_sym = ticker.split(":")[-1] if ":" in ticker else ticker
                    dynamic_watchlist.append(clean_sym)
                    
            # Eğer borsa kapalıysa liste boş olabilir, bu durumda kriptolara (default) düş
            if not dynamic_watchlist:
                dynamic_watchlist = ["BTCUSDT", "ETHUSDT", "SOLUSDT"]

            live_data = await asyncio.to_thread(tradingview_live_client.fetch_live_market_data)
            
            # --- YÜKSEK KONSEY: AÇIK POZİSYON ÖNGÖRÜ SÜZGECİ (MANDATORY) ---
            from services.market_feed.live_stream import live_trade_manager
            open_pos_list = [p for p in live_trade_manager.positions.values() if p.status == "OPEN"]
            if open_pos_list:
                logger.info(f"👁️ [YÜKSEK KONSEY] {len(open_pos_list)} Aktif Pozisyon 'Öngörü Süzgecinden' (Dinamik Risk/Karar Denetimi) geçiriliyor...")
                for pos in open_pos_list:
                    # Basit/Hızlı bir tehlike denetimi (Hacim çöküşü veya trend dönüşü var mı?)
                    pos_data = live_data.get(pos.symbol)
                    if pos_data:
                        pos_rsi = pos_data.get("RSI|60", 50)
                        pos_vol = pos_data.get("volume_ratio", 1.0)
                        pos_macd = pos_data.get("MACD.macd|60", 0)
                        pos_signal = pos_data.get("MACD.signal|60", 0)
                        
                        # 1. Aşama: Komite & Ajanlar (Çoklu İndikatör Süzgeci)
                        tehlike_puani = 0
                        if pos_vol < 0.6: tehlike_puani += 30  # Hacim çöküşü (Balina çıkışı)
                        if pos_macd < pos_signal: tehlike_puani += 30  # MACD Sat sinyali (Momentum kaybı)
                        if pos_rsi > 72: tehlike_puani += 40  # Aşırı Şişme (Dönüş kapıda)
                        elif pos_rsi < 35 and float(getattr(pos, 'unrealized_pnl', 0)) < 0: tehlike_puani += 40 # Düşen Bıçak
                        
                        # 2. Aşama: Konsey Kesin Hükmü (Tam Otonom Çıkış)
                        if tehlike_puani >= 60:
                            logger.warning(f"🚨 [KOMİTE ALARMI] {pos.symbol} için tehlike puanı {tehlike_puani}! Dinamik iz sürücü aktif, tasfiye (Likit) başlatılıyor...")
                            
                            # Tam otonom tereddütsüz çıkış (Market Sell - Kâr Realizasyonu veya Zarar Kes)
                            from services.broker.alpaca_client import alpaca_client
                            if alpaca_client.api_key:
                                try:
                                    import requests
                                    url = f"{alpaca_client.base_url}/positions/{pos.symbol}"
                                    headers = {
                                        "APCA-API-KEY-ID": alpaca_client.api_key,
                                        "APCA-API-SECRET-KEY": alpaca_client.api_secret
                                    }
                                    res = requests.delete(url, headers=headers)
                                    if res.status_code in [200, 201]:
                                        logger.info(f"💥 [TAM OTONOM ÇIKIŞ] {pos.symbol} Konsey öngörüsüyle (Kâr/Zarar) tereddütsüz kapatıldı!")
                                        pos.status = "CLOSED_EARLY"
                                except Exception as e:
                                    logger.error(f"[OTONOM ÇIKIŞ HATASI] {pos.symbol} - {e}")
            

                            
            # Dinamik listede sörf yap
            for symbol in dynamic_watchlist:
                market_item = live_data.get(symbol)
                if not market_item or float(market_item.get("price", 0.0) or 0.0) <= 0:
                    logger.info(f"[SHADOW AI] {symbol} için doğrulanmış fiyat yok; cache yazılmadı.")
                    continue

                pre_analysis_probe = WebhookSignal(
                    symbol=symbol,
                    action="BUY", # Sadece piyasayı analiz etmek için yön tayini (temsili)
                    price=float(market_item["price"]),
                    quantity=1.0, # Miktar analiz için önemsizdir
                    passphrase=settings.passphrase,
                    timeframe="15m",
                    timestamp_ms=int(time.time() * 1000),
                    indicators={
                        key: value for key, value in market_item.items()
                        if key in {"rsi", "macd", "atr_pct", "adx", "volume_ratio", "cmf"}
                        and isinstance(value, (int, float))
                    }
                )
                try:
                    audit_result = await asyncio.to_thread(
                        financial_agent.audit_tradingview_signal_concurrently,
                        pre_analysis_probe
                    )
                    
                    # Cache'e yaz
                    analyzer_agent.shadow_analysis_cache[symbol] = {
                        "skills_audit": audit_result,
                        "agent_verdict": "PRE_COGNITIVE_READY",
                        "_timestamp": time.time()
                    }
                    logger.info(f"🔮 [SHADOW AI] {symbol} gölge analizi tamamlandı (Skor: {audit_result.get('overall_skill_score', 0)}).")
                    
                    # OTONOM AVLAMA MODÜLÜ (Gölge Arena Kendi Kendine Öğrenim - OYUN HAVUZU)
                    # Kullanıcı İsteği: "sanal işlem süreci normal aktif alpaca canlı yapacagı işlemlerden bagımsız olacak, deneyim havuzu olmalı"
                    score = audit_result.get('overall_skill_score', 0)
                    if score >= 40: 
                        logger.info(f"⚔️ [GÖLGE ARENA] {symbol} Otonom Oyun Havuzunda (Playground) işleme giriliyor! Skor: {score}")
                        
                        import uuid
                        from datetime import datetime, timezone
                        from services.market_feed.live_stream import ActivePosition, live_trade_manager
                        from services.risk_engine.market_hours import market_hours_validator
                        
                        entry_pr = float(market_item["price"])
                        # OTONOM ÖĞRENİM KORUMASI: Piyasa kapalıyken sahte işlem (shadow trade) açmayı reddet.
                        is_open, _, _ = market_hours_validator.is_market_open(symbol)
                        if not is_open:
                            logger.info(f"🛑 [SHADOW REJECTED] {symbol} piyasası kapalı. Gölge Arena'ya alınmadı.")
                            continue

                        # Eğer zaten aktif bir Gölge Arena pozisyonu yoksa aç
                        if symbol not in live_trade_manager.shadow_positions:
                            new_shadow_pos = ActivePosition(
                                id=f"SHADOW_{uuid.uuid4().hex[:6].upper()}",
                                symbol=symbol,
                                market="BIST" if market_hours_validator.get_market_type(symbol) == "BIST" else "CRYPTO",
                                side="BUY",
                                entry_price=entry_pr,
                                current_price=entry_pr,
                                quantity=100.0 / entry_pr if entry_pr > 0 else 0,
                                nominal_value=100.0,
                                target_profit_price=entry_pr * 1.05,
                                stop_loss_price=entry_pr * 0.97,
                                break_even_trigger_price=entry_pr * 1.015,
                                opened_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
                                confidence_score=score,
                                entry_indicators={"score": score, "market_regime": audit_result.get("market_regime", "BİLİNMEYEN")}
                            )
                            live_trade_manager.shadow_positions[symbol] = new_shadow_pos
                            logger.info(f"⚔️ [GÖLGE ARENA] {symbol} sanal test havuzunda işleme alındı! Dinamik iz sürücü gerçek zamanlı takip edecek.")
                        else:
                            logger.debug(f"[GÖLGE ARENA] {symbol} zaten test havuzunda aktif, yeni işlem açılmadı.")
                except Exception as e:
                    logger.warning(f"⚠️ [SHADOW AI] {symbol} güncellenirken hata: {e}")
                
                # API limitlerini zorlamamak için semboller arası bekleme
                await asyncio.sleep(2)
                
        except Exception as e:
            logger.error(f"[SHADOW SCANNER] Döngü hatası: {e}")
            
        await asyncio.sleep(30)

app = FastAPI(title="TradingView AI Webhook Gateway, Risk Engine & 10-Skill Financial AI Analyst")

from fastapi.exceptions import RequestValidationError
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    errors = exc.errors()
    structured_errors = []
    for e in errors:
        loc = " -> ".join([str(l) for l in e.get("loc", [])])
        msg = e.get("msg", "")
        structured_errors.append(f"Field '{loc}': {msg}")
    
    error_summary = " | ".join(structured_errors)
    logger.error(f"🛑 [WEBHOOK ŞEMA İHLALİ] Yapısal Hata veya Eksik Veri: {error_summary}")
    
    return JSONResponse(
        status_code=422,
        content={
            "status": "REJECTED",
            "reason": "Payload validation failed (JSON Schema/Pydantic).",
            "details": structured_errors
        }
    )

from services.market_feed.live_stream import live_trade_manager
@app.on_event("startup")
async def startup_event():
    logger.info("[STARTUP] Başlatılıyor: 7/24 Kesintisiz Otonom Strateji Motoru Arka Planda Aktif Edildi.")
    asyncio.create_task(tv_auto_runner.start_continuous_background_loop())
    
    # Shadow AI (Gölge Zeka) Cache Tarayıcısını Başlat
    asyncio.create_task(start_shadow_scanner())
    
    # Superalgos Shadow Training Loop (Geçmiş İşlemlerle Walk-Forward Validation)
    from services.ai.shadow_training_loop import shadow_trainer
    asyncio.create_task(shadow_trainer.start_training_loop(interval_seconds=3600))
    
    # OKX Agent Trade Kit - AI Direct Risk Manager
    from services.ai.ai_risk_manager import ai_risk_manager
    asyncio.create_task(ai_risk_manager.start_risk_loop(interval_seconds=120))
    
    # --- OTONOM MOTOR ENTEGRASYONLARI ---
    # LLM Dış Ses (Voice Engine) Başlat
    from services.engine.voice_engine import ai_voice_engine
    # Uygulama açılır açılmaz ilk dış sesi üret
    asyncio.create_task(ai_voice_engine.generate_voice())
    # Sonra da 5 dakikalık döngüyü başlat
    asyncio.create_task(ai_voice_engine.start_voice_loop())

    # 1. L2 Orderbook Asenkron Tarayıcı (Spoofing Algılayıcı) - Geçici Olarak Devre Dışı
    # from services.engine.l2_orderbook_engine import l2_orderbook_engine
    # asyncio.create_task(l2_orderbook_engine.start_l2_stream())
    logger.info("[STARTUP] L2 Orderbook Otonom Tarayıcı Devre Dışı Bırakıldı, Dış Ses Aktif.")

    # 2. StatArb Engine Döngüsü (Her 5 dakikada bir tarama)
    async def run_advanced_engines():
        from services.engine.stat_arb_engine import stat_arb_engine
        while True:
            try:
                if live_trade_manager.market_prices:
                    stat_arb_engine.scan_for_opportunities(live_trade_manager.market_prices)
            except Exception as e:
                logger.error(f"[Advanced Engines Loop] Hata: {e}")
            await asyncio.sleep(300)

    asyncio.create_task(run_advanced_engines())
    
    # 3. Ana AI Trade Engine Döngüsü (Otonom Avcı ve Makro Analiz)
    async def run_ai_trade_engine():
        while True:
            try:
                # Otonom avcı, makro risk ve YZ sentezlerini çalıştırır
                await asyncio.to_thread(live_trade_manager.get_live_prices, fetch_new=True)
                
                # YENİ: Askıda kalan, dolmayan emirlerin tespiti ve İptal/Vazgeçilmesi
                await asyncio.to_thread(live_trade_manager.check_and_cancel_stale_orders)
            except Exception as e:
                logger.error(f"[AI Trade Engine Loop] Hata: {e}")
            await asyncio.sleep(4) # Hızlandırıldı: Dashboard'un canlı akması için 4 saniyeye düşürüldü

    asyncio.create_task(run_ai_trade_engine())
    
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
    # try:
    #     from services.broker.alpaca_data_stream import start_alpaca_data_stream
    #     asyncio.create_task(start_alpaca_data_stream())
    #     logger.info("[STARTUP] Alpaca Data Stream (Canlı Fiyat & Dinamik Makas) Dinleyicisi Başlatıldı.")
    # except Exception as e:
    #     logger.error(f"[STARTUP] Alpaca Data Stream Başlatılamadı: {e}")

    # 4. TIER-1 Otonom Motor (Astra-6 V2.0 SOTA)
    try:
        from services.engine.autonomous_loop import autonomous_engine
        asyncio.create_task(autonomous_engine.start())
        logger.info("🟢 [STARTUP] Tier-1 SOTA Otonom Motor Başlatıldı (Kusursuz Avcı).")
    except Exception as e:
        logger.error(f"[STARTUP] Otonom Motor Başlatılamadı: {e}")

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

@app.get("/shadow", response_class=HTMLResponse)
async def get_shadow_dashboard(request: Request):
    """
    Tier-1 Gölge Arena ve ML İç Ses (Monologue) Dashboard
    """
    return templates.TemplateResponse(
        request=request,
        name="shadow_dashboard.html",
        context={}
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


@app.on_event("startup")
async def startup_accountability_check():
    import os
    print("\n" + "="*70)
    print("!!! SİSTEM HATIRLATMASI (ADMİN'DEN KAZINAN SABİT HAFIZA) !!!")
    print("Geçmiş işlem değerlendirmelerinin sonucu:")
    print("1. Bireysel Hisseler (NVDA, ANET, CDNS) = KÂRDA.")
    print("2. Otonom Kriptolar (NEAR, RENDER, SOL, CRV, FIL) = ZARARDA.")
    print("3. Aşırı İşlem (DIA) = -3$ Komisyon Kaybı (Bot Hatası).")
    print("KURAL: Geçmişi unutup yeni heyecanlar satmak yasaklanmıştır.")
    print("Döngüselliği kır. Hüsranı tekrar etme. Profesyonel ol.")
    print("="*70 + "\n")
    try:
        portfolio_path = os.path.join("scratch", "master_portfolio.json")
        if os.path.exists(portfolio_path):
            with open(portfolio_path, "r", encoding="utf-8") as f:
                app.state.master_portfolio = json.load(f)
                print("[✓] Master Portföy (Zarar Durumu) sisteme başarıyla mühürlendi.")
    except Exception as e:
        print(f"[X] Hafıza yüklenemedi: {e}")

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
app.include_router(ai_chat_router)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
