with open('routers/position_router.py', 'r', encoding='utf-8') as f:
    text = f.read()

clock_endpoint = '''
@router.get("/clock")
async def get_alpaca_clock():
    \"\"\"
    Alpaca'dan canlı piyasa saati ve durumunu çeker
    \"\"\"
    if settings.trading_mode in ["LIVE", "PAPER"]:
        from services.broker.factory import get_broker
        broker = get_broker(settings.active_broker, paper=(settings.trading_mode == "PAPER"))
        if broker and broker.api:
            try:
                clock = broker.api.get_clock()
                return {
                    "status": "success",
                    "is_open": clock.is_open,
                    "timestamp": clock.timestamp.isoformat(),
                    "next_open": clock.next_open.isoformat(),
                    "next_close": clock.next_close.isoformat()
                }
            except Exception as e:
                import logging
                logging.error(f"Alpaca clock fetch error: {e}")
                
    # Fallback to local time
    import datetime
    now = datetime.datetime.now(datetime.timezone.utc)
    return {
        "status": "fallback",
        "is_open": True,  # Mocked
        "timestamp": now.isoformat(),
        "next_open": now.isoformat(),
        "next_close": now.isoformat()
    }
'''

# append to the end of the file
if 'get_alpaca_clock' not in text:
    with open('routers/position_router.py', 'a', encoding='utf-8') as f:
        f.write("\n" + clock_endpoint)
    print("Added /clock endpoint.")
else:
    print("Endpoint already exists.")
