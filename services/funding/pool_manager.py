from core.logger import logger
from typing import Dict, Any

class PoolManager:
    """
    Manages the master trading pool and distributes PnL among investors
    based on their share percentages.
    
    This is currently a skeleton module for future Crowdfunding platform capabilities.
    """
    
    def __init__(self):
        self.total_pool_value = 0.0
        self.investors = {} # user_id -> shares
        
    def add_funds(self, user_id: int, amount_usd: float) -> float:
        """Adds funds for an investor and calculates their new shares."""
        # TODO: Connect to models/users.py Database
        logger.info(f"[Crowdfunding] User {user_id} added ${amount_usd} to the pool.")
        return amount_usd

    def distribute_profit(self, trade_profit_usd: float, developer_fee_pct: float = 25.0) -> Dict[str, float]:
        """
        When a trade closes in profit, this calculates the developer's fee 
        and distributes the rest to investors proportional to their shares.
        """
        if trade_profit_usd <= 0:
            return {}
            
        dev_fee = trade_profit_usd * (developer_fee_pct / 100.0)
        distributable_profit = trade_profit_usd - dev_fee
        
        logger.info(f"[Crowdfunding] PnL Split: Developer gets ${dev_fee:.2f}, Investors share ${distributable_profit:.2f}")
        return {
            "developer_fee": dev_fee,
            "investor_pool": distributable_profit
        }

pool_manager = PoolManager()
