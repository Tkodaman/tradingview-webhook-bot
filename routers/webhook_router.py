import time
from fastapi import APIRouter, Depends, Request, HTTPException, status
from fastapi.responses import JSONResponse
from core.security import verify_ip, verify_passphrase
from core.logger import logger
from schemas.webhook import WebhookSignal
from services.order_router import process_order
from core.config import settings
from services.broker.alpaca_client import alpaca_client

router = APIRouter()

# Debounce cache: { "SIGNAL_ID": timestamp_of_insertion }
processed_signals = {}

@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "TradingView Webhook Gateway, Autonomous Risk Analyzer & 10-Skill AI Analyst",
        "trading_mode": settings.trading_mode,
        "max_risk_allowed": settings.max_risk_score_allowed if hasattr(settings, 'max_risk_score_allowed') else 100
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
    
    # 0. SİSTEM KORUMA MODU (STATE RECONCILER)
    from services.market_feed.live_stream import live_trade_manager
    if getattr(live_trade_manager, "is_paused", False):
        logger.warning(f"🛑 [WEBHOOK REDDEDİLDİ] Sistem Koruma Modunda. Gelen sinyal yoksayıldı: {signal.symbol}")
        raise HTTPException(status_code=403, detail=f"Sistem Koruma Modunda (Pause): {getattr(live_trade_manager, 'pause_reason', '')}")
    
    # 1. GÜVENLİK TOKEN KONTROLÜÜ
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
            
    # 3. IDEMPOTENCY & DEBOUNCE (TEKRAR KORUMASI)
    # Temizleme: 5 dakikadan eski sinyalleri önbellekten sil
    keys_to_delete = [k for k, v in processed_signals.items() if current_time_ms - v > 300000]
    for k in keys_to_delete:
        del processed_signals[k]
        
    signal_id = f"{signal.symbol.upper()}_{signal.timestamp_ms}_{signal.action}" if signal.timestamp_ms else f"{signal.symbol.upper()}_{signal.action}_{current_time_ms // 3000}"
    
    if signal_id in processed_signals:
        logger.warning(f"🪚 DUPLICATE SIGNAL REJECTED: {signal_id} already processed!")
        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={"status": "REJECTED", "reason": "Duplicate signal (Idempotency active)."}
        )
    processed_signals[signal_id] = current_time_ms

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
