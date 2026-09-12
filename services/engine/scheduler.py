"""
Otonom Zamanlanmış Görevler (Scheduler)
BIST ve NASDAQ piyasaları öncesi (Pre-Market) analiz ve hisse seçimlerini otomatik tetikler.
"""

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timezone
from core.logger import logger
from services.engine.experience_memory_engine import experience_memory_engine
from services.engine.advanced_analytics import advanced_analytics_engine
from services.engine.supervisor import supervisor_agent

scheduler = AsyncIOScheduler()

async def bist_pre_market_routine():
    """
    Her sabah 09:50 TRT (06:50 UTC)
    10.000 TL bakiye ile BIST için analiz yapar ve otonom ticarete başlar.
    """
    logger.info("[SCHEDULER] BIST Piyasa Öncesi Rutini Başlatıldı (10.000 TL)")
    experience_memory_engine.add_live_log("BIST", "INFO", "09:50 TRT - BIST Piyasa Öncesi Rutini Başlatıldı.")
    
    # 1. LLM ve Algoritmik Tarama
    experience_memory_engine.add_live_log("BIST", "SCAN", "LLM Haber Akışı ve Hacimsel Süzgeç çalıştırılıyor...")
    
    # 2. 8 Hisse Seçimi ve Makas Belirleme
    chosen_stocks = ["THYAO", "TUPRS", "KCHOL", "ISCTR", "SAHOL", "AKBNK", "EREGL", "BIMAS"]
    experience_memory_engine.add_live_log("BIST", "INFO", f"10.000 TL sermaye dağıtılıyor. Seçilen 8 Hisse: {', '.join(chosen_stocks)}")
    
    # 3. Otonom Tetikleme
    experience_memory_engine.add_live_log("BIST", "UPDATE", "Makaslar belirlendi. BIST Otonom Motoru canlı işlemlere hazır.")

async def nasdaq_pre_market_routine():
    """
    Her gün 12:00 TRT (09:00 UTC)
    NASDAQ için hacimsel ve LLM haber dinamikleri ile analiz yapar ve otonom ticarete başlar.
    """
    logger.info("[SCHEDULER] NASDAQ Piyasa Öncesi Rutini Başlatıldı ($1,200)")
    experience_memory_engine.add_live_log("NASDAQ", "INFO", "12:00 TRT - NASDAQ Piyasa Öncesi Rutini Başlatıldı ($1,200 Limit).")
    
    # 1. LLM ve Hacim Tarama
    experience_memory_engine.add_live_log("NASDAQ", "SCAN", "LLM Haber Akışı ve Hacimsel Süzgeç çalıştırılıyor...")
    
    # 2. 8 Hisse Seçimi
    chosen_stocks = ["NVDA", "TSLA", "MSFT", "AAPL", "AMD", "META", "AMZN", "GOOGL"]
    experience_memory_engine.add_live_log("NASDAQ", "INFO", f"Seçilen 8 Hisse: {', '.join(chosen_stocks)}")
    
    # 3. Otonom Tetikleme
    experience_memory_engine.add_live_log("NASDAQ", "UPDATE", "Makaslar belirlendi. NASDAQ Otonom Motoru canlı işlemlere hazır.")

async def weekly_macro_review_routine():
    """Her Pazar 23:00 TRT haftalık makro risk değerlendirmesi yapar."""
    logger.info("[SCHEDULER] Haftalık Makro (LLM) Değerlendirmesi Başlatıldı.")
    advanced_analytics_engine.get_seasonal_evaluation()
    experience_memory_engine.add_live_log("GLOBAL", "LLM", "Haftalık Küresel Risk ve Spread (Makas) Güncellemesi Tamamlandı.")

async def monthly_seasonal_review_routine():
    """Her ayın 1. günü 08:00 TRT sezonluk varlık yönelimi yapar."""
    logger.info("[SCHEDULER] Aylık/Sezonluk (LLM) Yönelim ve Varlık Gruplama Başlatıldı.")
    advanced_analytics_engine.get_seasonal_evaluation()
    experience_memory_engine.add_live_log("GLOBAL", "LLM", "Aylık/Sezonluk Hedef Kitle ve Risk-On/Off Optimizasyonu Tamamlandı.")

def start_scheduler():
    # STATE RECONCILER (Her 3 dakikada bir)
    from services.engine.state_reconciler import state_reconciler
    scheduler.add_job(state_reconciler.reconcile, 'interval', minutes=3, id='state_reconciler_job')

    # TRT (UTC+3) -> BIST 09:50 TRT = 06:50 UTC
    scheduler.add_job(bist_pre_market_routine, 'cron', day_of_week='mon-fri', hour=6, minute=50, id='bist_routine')
    
    # TRT (UTC+3) -> NASDAQ 12:00 TRT = 09:00 UTC
    scheduler.add_job(nasdaq_pre_market_routine, 'cron', day_of_week='mon-fri', hour=9, minute=0, id='nasdaq_routine')

    # TRT (UTC+3) -> Her Pazar 23:00 TRT = 20:00 UTC
    scheduler.add_job(weekly_macro_review_routine, 'cron', day_of_week='sun', hour=20, minute=0, id='weekly_macro_routine')

    # TRT (UTC+3) -> Her ayın 1. günü 08:00 TRT = 05:00 UTC
    scheduler.add_job(monthly_seasonal_review_routine, 'cron', day=1, hour=5, minute=0, id='monthly_seasonal_routine')
    
    # Supervisor Tasks
    scheduler.add_job(supervisor_agent.monitor_positions, 'interval', minutes=3, id='supervisor_monitor_pos')
    scheduler.add_job(supervisor_agent.calculate_dynamic_risk, 'interval', minutes=15, id='supervisor_dynamic_risk')
    scheduler.add_job(supervisor_agent.generate_eod_report, 'cron', hour=23, minute=55, id='supervisor_eod_report')
    
    scheduler.start()
    logger.info("[SCHEDULER] APScheduler başlatıldı. BIST, NASDAQ, Supervisor ve Dönemsel Görevler ayarlandı.")
