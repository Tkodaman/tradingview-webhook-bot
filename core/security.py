from fastapi import Request, HTTPException
from core.config import settings
import logging

logger = logging.getLogger("security")

async def verify_ip(request: Request):
    client_ip = request.client.host
    # If behind proxy (ngrok), use x-forwarded-for
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        client_ip = forwarded_for.split(",")[0].strip()
        
    if client_ip not in settings.get_allowed_ips_list:
        logger.warning(f"Blocked request from unauthorized IP: {client_ip}")
        raise HTTPException(status_code=403, detail="Forbidden: IP not allowed")
    return True

def verify_passphrase(passphrase: str):
    if passphrase != settings.passphrase:
        logger.warning("Blocked request with invalid passphrase")
        raise HTTPException(status_code=401, detail="Unauthorized: Invalid passphrase")
    return True


