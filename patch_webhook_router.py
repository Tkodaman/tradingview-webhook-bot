with open('routers/webhook_router.py', 'r', encoding='utf-8') as f:
    text = f.read()

new_logic = '''import time
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import JSONResponse
from core.security import verify_ip, verify_passphrase
from core.logger import logger
from schemas.webhook import WebhookSignal
from services.order_router import process_order
from core.config import settings
from services.broker.alpaca_client import alpaca_client

router = APIRouter()

# Debounce cache: { "SYMBOL": timestamp_of_last_signal }
debounce_cache = {}

@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "TradingView Webhook Gateway, Autonomous Risk Analyzer & 10-Skill AI Analyst",
        "trading_mode": settings.trading_mode,
        "max_risk_allowed": settings.max_risk_allowed if hasattr(settings, 'max_risk_allowed') else 100
    }

@router.get("/webhook")
async def webhook_info():
    return {
        "status": "active_and_ready",
        "message": "TradingView Webhook Uç Noktası Canlı ve Aktif!",
        "accepted_method": "POST"
    }

@router.post("/webhook", dependencies=[Depends(verify_ip)])
async def webhook_receiver(signal: WebhookSignal, request: Request):
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "127.0.0.1").split(",")[0].strip()
    logger.info(f"Received webhook from {client_ip}: {signal.model_dump_json()}")
    
    # 1. GÜVENLİK TOKEN KONTROLÜ
    if signal.security_token and hasattr(settings, "webhook_security_token"):
        if signal.security_token != settings.webhook_security_token:
            logger.warning(f"❌ INVALID SECURITY TOKEN from {client_ip}")
            raise HTTPException(status_code=401, detail="Invalid security token")
    
    verify_passphrase(signal.passphrase)
    
    current_time_ms = int(time.time() * 1000)
    
    # 2. LATENCY (GECİKME) KONTROLÜ
    if signal.timestamp_ms:
        latency = current_time_ms - signal.timestamp_ms
        if latency > 1500:
            logger.warning(f"⏳ STALE SIGNAL REJECTED: {signal.symbol} - Latency: {latency}ms")
            return JSONResponse(
                status_code=status.HTTP_406_NOT_ACCEPTABLE,
                content={"status": "REJECTED", "reason": f"Stale signal. Latency {latency}ms > 1500ms"}
            )
            
    # 3. DEBOUNCE (TESTERE) KORUMASI
    last_time = debounce_cache.get(signal.symbol.upper(), 0)
    if current_time_ms - last_time < 3000:
        logger.warning(f"🪚 DEBOUNCE REJECTED: {signal.symbol} - Signals arriving too fast!")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"status": "REJECTED", "reason": "Debounce protection active. Signal blocked."}
        )
    debounce_cache[signal.symbol.upper()] = current_time_ms

    # 4. SPREAD GUARD KONTROLÜ (Bid-Ask Makası)
    spread_pct = alpaca_client.get_bid_ask_spread(signal.symbol)
    if spread_pct > 0.15:
        logger.warning(f"🛑 SPREAD GUARD ACTIVE: {signal.symbol} spread is {spread_pct:.3f}% > 0.15%. Order deferred to WAIT state.")
        return JSONResponse(
            status_code=status.HTTP_202_ACCEPTED,
            content={"status": "WAIT", "reason": f"High spread ({spread_pct:.3f}%). Slippage risk prevented."}
        )

    # 5. NORMAL İŞLEM SÜRECİ
    result = process_order(signal)
    return result
'''

with open('routers/webhook_router.py', 'w', encoding='utf-8') as f:
    f.write(new_logic)
