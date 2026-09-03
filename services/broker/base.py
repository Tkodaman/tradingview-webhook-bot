from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseBroker(ABC):
    """
    Abstract base class for all broker bridges.
    Any new broker (Alpaca, Interactive Brokers, Midas, etc.) must implement this interface.
    """
    
    @abstractmethod
    def get_account_balance(self) -> float:
        """Returns available buying power in USD/TRY."""
        pass

    @abstractmethod
    def place_market_order(self, symbol: str, side: str, qty: float) -> Dict[str, Any]:
        """Places a simple market order."""
        pass
        
    @abstractmethod
    def place_bracket_order(self, symbol: str, side: str, qty: float, 
                            take_profit_price: float, stop_loss_price: float) -> Dict[str, Any]:
        """Places an entry order with attached take profit and stop loss."""
        pass
        
    @abstractmethod
    def close_position(self, symbol: str) -> Dict[str, Any]:
        """Closes an open position entirely."""
        pass
        
    @abstractmethod
    def get_open_positions(self) -> list:
        """Returns a list of currently open positions."""
        pass
