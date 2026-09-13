import logging
from core.config import settings
from services.broker.factory import get_broker
from services.market_feed.live_stream import live_trade_manager

logger = logging.getLogger("bot_logger")

class StateReconciler:
    def __init__(self):
        self.broker = get_broker(settings.active_broker, paper=(settings.trading_mode == "PAPER"))
        
    def reconcile(self):
        if settings.trading_mode not in ["LIVE", "PAPER"]:
            return
            
        if not self.broker or not self.broker.api:
            return
            
        logger.info("[RECONCILER] Durum Mutabakatı (State Reconciler) başlıyor...")
        
        try:
            raw_positions = self.broker.get_open_positions()
            if raw_positions is None:
                logger.warning("[RECONCILER] Alpaca returned None for positions (Network error?). Skipping this cycle.")
                return
                
            broker_symbols = {p.get("symbol") for p in raw_positions if p.get("symbol")}
            
            # Format local symbols to match broker symbols (e.g. LINKUSDT -> LINKUSD)
            local_open_positions = set()
            for pos in live_trade_manager.positions.values():
                if pos.status == "OPEN":
                    formatted_sym = self.broker._format_symbol(pos.symbol) if hasattr(self.broker, "_format_symbol") else pos.symbol
                    local_open_positions.add(formatted_sym)
            
            
            desync_reasons = []
            
            # Check for positions that are open locally but missing from broker
            missing_on_broker = local_open_positions - broker_symbols
            if missing_on_broker:
                desync_reasons.append(f"Lokalde açık ancak Broker'da eksik: {missing_on_broker}")
                
            # Check for positions open on broker but missing locally
            missing_locally = broker_symbols - local_open_positions
            if missing_locally:
                # This could happen if user opens positions manually on Alpaca, or we missed a webhook.
                desync_reasons.append(f"Broker'da açık ancak lokalde eksik: {missing_locally}")
                
            # Check balance 
            real_balance = self.broker.get_account_balance()
            if real_balance < 100.0:  # Critical low balance check
                desync_reasons.append(f"Kritik Düşük Bakiye: ${real_balance}")
                
            if desync_reasons:
                reason_str = " | ".join(desync_reasons)
                logger.error(f"🚨 [RECONCILER DESYNC] Mutabakat Hatası Tespit Edildi: {reason_str}")
                
                # Protect system
                live_trade_manager.is_paused = True
                live_trade_manager.pause_reason = reason_str
                logger.critical("🛑 [RECONCILER] SİSTEM KORUMA MODUNA ALINDI! YENİ İŞLEMLER (WEBHOOK) DURDURULDU.")
            else:
                logger.info("[RECONCILER] Mutabakat Başarılı. Sistem Senkronize.")
                
                # Auto-resume logic if enabled
                if live_trade_manager.is_paused and live_trade_manager.auto_resume_reconciler:
                    logger.info("✅ [RECONCILER] Hata durumu çözüldü. Sistem koruma modundan çıkarılıyor (Auto-Resume).")
                    live_trade_manager.is_paused = False
                    live_trade_manager.pause_reason = ""
                    
        except Exception as e:
            logger.error(f"[RECONCILER ERROR] Mutabakat sırasında hata: {e}")
            
state_reconciler = StateReconciler()
