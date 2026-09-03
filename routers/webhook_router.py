from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse
from core.security import verify_ip, verify_passphrase
from core.logger import logger
from schemas.webhook import WebhookSignal
from services.order_router import process_order
from core.config import settings

router = APIRouter()

@router.get("/health")
async def health_check():
    return {
        "status": "ok",
        "service": "TradingView Webhook Gateway, Autonomous Risk Analyzer & 10-Skill AI Analyst",
        "trading_mode": settings.trading_mode,
        "max_risk_allowed": settings.max_risk_score_allowed
    }

@router.get("/webhook")
async def webhook_info():
    return {
        "status": "active_and_ready",
        "message": "TradingView Webhook Uç Noktası Canlı ve Aktif! TradingView alarmlarınızı HTTP POST ile bu adrese gönderin.",
        "accepted_method": "POST",
        "payload_format": "JSON",
        "dashboard": "/"
    }

@router.post("/webhook", dependencies=[Depends(verify_ip)])
async def webhook_receiver(signal: WebhookSignal, request: Request):
    client_ip = request.headers.get("X-Forwarded-For", request.client.host if request.client else "127.0.0.1").split(",")[0].strip()
    logger.info(f"Received webhook from {client_ip}: {signal.model_dump_json()}")
    
    verify_passphrase(signal.passphrase)
    
    result = process_order(signal)
    return result
