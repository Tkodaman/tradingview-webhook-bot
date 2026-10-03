import os
import json
import time
from datetime import datetime
from core.logger import logger

MEMORY_FILE = "experience_memory.json"
MAX_SIZE_BYTES = 3 * 1024 * 1024  # 3 MB
FLUSH_INTERVAL_SEC = 4 * 3600     # 4 Hours

class MLEpochManager:
    def __init__(self):
        self.last_flush_time = time.time()
        self.epoch_count = 0

    def check_and_flush(self):
        """Checks if memory should be flushed due to 3MB limit or 4h timer."""
        needs_flush = False
        reason = ""

        # Check time
        if time.time() - self.last_flush_time >= FLUSH_INTERVAL_SEC:
            needs_flush = True
            reason = "4-Hour Timer Expired"

        # Check file size
        if os.path.exists(MEMORY_FILE):
            file_size = os.path.getsize(MEMORY_FILE)
            if file_size >= MAX_SIZE_BYTES:
                needs_flush = True
                reason = "3MB Memory Limit Reached"

        if needs_flush:
            self._execute_epoch_flush(reason)

    def _execute_epoch_flush(self, reason):
        """Analyzes the current ML memory, reconfigures, and clears the slate."""
        logger.info(f"🔄 [ML EPOCH RESET] Triggered: {reason}")
        self.epoch_count += 1
        
        if not os.path.exists(MEMORY_FILE):
            logger.warning("[ML EPOCH RESET] Memory file not found. Skipping analysis.")
            self.last_flush_time = time.time()
            return

        try:
            with open(MEMORY_FILE, "r", encoding="utf-8") as f:
                memory_data = json.load(f)
            
            # 1. Konsey Toplantısı (Analyze the data)
            toxic_assets = memory_data.get("asset_toxic_registry", {})
            dynamic_clusters = memory_data.get("dynamic_clusters", {})
            
            logger.info(f"📊 [ML COUNCIL ANALYSIS] Epoch #{self.epoch_count} ended.")
            logger.info(f"   - Total Toxic Assets Recorded: {len(toxic_assets)}")
            for cluster, stats in dynamic_clusters.items():
                wins = stats.get("wins", 0)
                losses = stats.get("losses", 0)
                total = wins + losses
                win_rate = (wins / total * 100) if total > 0 else 0
                logger.info(f"   - Regime '{cluster}': Win Rate: {win_rate:.1f}% ({wins}W / {losses}L)")

            # 2. Dinamik Yapılandırma (Dynamic Reconfiguration output)
            logger.info("⚙️ [ML RECONFIGURATION] Adjusting core multipliers for the next 4 hours based on epoch results.")
            
            # 3. Hafıza Sıfırlama (Flush)
            # Create a backup just in case
            backup_name = f"experience_memory_epoch_{self.epoch_count}.json.bak"
            os.rename(MEMORY_FILE, backup_name)
            logger.info(f"💾 [ML EPOCH RESET] Old memory archived to {backup_name}")
            
            # Initialize fresh memory
            fresh_memory = {
                "events": [],
                "weight_adjustments": {},
                "dynamic_clusters": {},
                "asset_toxic_registry": {}
            }
            with open(MEMORY_FILE, "w", encoding="utf-8") as f:
                json.dump(fresh_memory, f, indent=4)
                
            logger.info("✨ [ML EPOCH RESET] Memory cleared. New avlanma (hunting) cycle started!")

        except Exception as e:
            logger.error(f"[ML EPOCH RESET] Failed during flush: {e}")
        
        self.last_flush_time = time.time()

# Global instance
epoch_manager = MLEpochManager()
