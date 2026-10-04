import time
import threading
import socket
from datetime import datetime, timezone
from core.database import db_manager
from core.logger import logger

class HAManager:
    def __init__(self):
        self.node_id = socket.gethostname() + "_bot"
        self.is_leader = False
        self.running = False
        self._thread = None
        self.heartbeat_interval = 10
        self.takeover_timeout = 90
        
        # Local is preferred leader, VPS is secondary
        self.is_preferred_leader = "vps" not in self.node_id.lower() and "instance" not in self.node_id.lower()

    def start(self):
        self.running = True
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        logger.info(f"[HA MANAGER] Started. Node ID: {self.node_id}. Preferred Leader: {self.is_preferred_leader}")

    def stop(self):
        self.running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _loop(self):
        while self.running:
            try:
                self._run_heartbeat()
            except Exception as e:
                logger.error(f"[HA MANAGER] Error in heartbeat loop: {e}")
            time.sleep(self.heartbeat_interval)

    def _run_heartbeat(self):
        now = time.time()
        
        # 1. Update our own heartbeat
        db_manager.update_heartbeat(self.node_id, now, self.is_preferred_leader)
        
        # 2. Get all heartbeats
        heartbeats = db_manager.get_all_heartbeats()
        
        active_nodes = []
        for hb in heartbeats:
            node = hb['node_id']
            last_seen = float(hb['last_seen'])
            preferred = hb['is_preferred_leader']
            db_time = float(hb.get('db_time', now))
            
            if db_time - last_seen < self.takeover_timeout:
                active_nodes.append((node, preferred, last_seen))

        if not active_nodes:
            self._set_leader(True)
            return

        # 3. Leader Election Logic
        # - If preferred leader is active, it wins.
        # - If preferred leader is dead, the secondary takes over.
        preferred_leaders = [n for n in active_nodes if n[1]]
        
        if preferred_leaders:
            # Preferred leader exists and is alive
            winning_node = preferred_leaders[0][0] # Just pick the first preferred if multiple
        else:
            # No preferred leader, pick the one with most recent last_seen
            active_nodes.sort(key=lambda x: x[2], reverse=True)
            winning_node = active_nodes[0][0]

        new_is_leader = (self.node_id == winning_node)

        if new_is_leader != self.is_leader:
            self._set_leader(new_is_leader)

    def _set_leader(self, state: bool):
        self.is_leader = state
        if state:
            logger.info(f"🏆 [HA MANAGER] {self.node_id} is now LEADER. Autonomous trading ENABLED.")
            # Reload state in case the other node modified positions
            from services.market_feed.live_stream import live_trade_manager
            live_trade_manager.load_state()
        else:
            logger.info(f"💤 [HA MANAGER] {self.node_id} is now FOLLOWER. Autonomous trading DISABLED. Standing by...")

ha_manager = HAManager()
