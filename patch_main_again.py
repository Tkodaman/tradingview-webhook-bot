with open('main.py', 'r', encoding='utf-8') as f:
    text = f.read()
import re
new_startup = '''
@app.on_event("startup")
async def startup_event():
    logger.info("[STARTUP] Başlatılıyor: 7/24 Kesintisiz Otonom Strateji Motoru Arka Planda Aktif Edildi.")
    asyncio.create_task(tv_auto_runner.start_continuous_background_loop())
    
    # Start WebSocket Broadcaster
    asyncio.create_task(live_data_broadcaster(live_trade_manager_instance))
    
    # Start Alpaca Trade Updates WebSocket (Zero-latency Close detection)
    try:
        from services.broker.alpaca_stream import start_alpaca_stream
        asyncio.create_task(start_alpaca_stream())
        logger.info("[STARTUP] Alpaca WS Trade Updates (Sıfır Gecikme) Dinleyicisi Başlatıldı.")
    except Exception as e:
        logger.error(f"[STARTUP] Alpaca WS Başlatılamadı: {e}")

    # Scheduler (BIST ve NASDAQ Zamanlanmış Görevleri)
    start_scheduler()
'''
text = re.sub(
    r'@app\.on_event\("startup"\)\s*async def startup_event\(\):\s*logger\.info\("\[STARTUP\] Başlatılıyor: 7/24 Kesintisiz Otonom Strateji Motoru Arka Planda Aktif Edildi\."\)\s*asyncio\.create_task\(tv_auto_runner\.start_continuous_background_loop\(\)\)\s*# Start WebSocket Broadcaster\s*asyncio\.create_task\(live_data_broadcaster\(live_trade_manager_instance\)\)\s*# Scheduler \(BIST ve NASDAQ Zamanlanmış Görevleri\)\s*start_scheduler\(\)',
    new_startup.strip(),
    text,
    flags=re.DOTALL
)
with open('main.py', 'w', encoding='utf-8') as f:
    f.write(text)
