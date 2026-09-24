import logging
logging.disable(logging.CRITICAL)
from fastapi.testclient import TestClient
from main import app

c = TestClient(app)
r = c.post('/api/engine/risk-mode', headers={'X-Forwarded-For': '127.0.0.1'}, json={'mode': 'NORMAL'})
d = r.json()
print("STATUS", r.status_code)
print("mode", d.get("current_mode"), "auto_trade_enabled", d.get("auto_trade_enabled"), "triggers", len(d.get("immediate_triggers", [])))

r2 = c.get('/api/engine/risk-mode', headers={'X-Forwarded-For': '127.0.0.1'})
print("GET after POST:", r2.json())
