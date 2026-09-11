import re

with open('routers/engine_router.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Append the new endpoint
new_endpoint = '''
from pydantic import BaseModel

class RiskModeRequest(BaseModel):
    mode: str

@router.post("/engine/risk-mode")
async def set_risk_mode(req: RiskModeRequest):
    \"\"\"
    Update the global AI risk threshold and multiplier logic mode.
    \"\"\"
    try:
        from core.config import settings
        valid_modes = ["AGGRESSIVE", "NORMAL", "TIGHT", "CONSERVATIVE"]
        mode = req.mode.upper()
        if mode in valid_modes:
            # Here we just save it to settings or global state.
            # In a real app we might persist this to DB.
            settings.trading_mode = mode # Just an example, usually you'd have a specific risk_mode field.
            return {"status": "success", "mode": mode}
        return {"status": "error", "message": "Invalid mode"}
    except Exception as e:
        return {"status": "error", "message": str(e)}
'''

if "/engine/risk-mode" not in content:
    with open('routers/engine_router.py', 'a', encoding='utf-8') as f:
        f.write(new_endpoint)
        print("Added new endpoint")
else:
    print("Endpoint already exists")

