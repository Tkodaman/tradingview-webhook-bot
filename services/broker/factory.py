from core.logger import logger
from services.broker.base import BaseBroker

# Broker singletons — paper ve live için ayrı instance
_alpaca_paper_instance = None
_alpaca_live_instance = None
_binance_paper_instance = None
_binance_live_instance = None

def get_broker(broker_name: str = "ALPACA", paper: bool = True) -> BaseBroker:
    """
    Factory function to get the appropriate broker bridge instance.
    Paper ve Live modları birbirinden izole tutulur — mod geçişinde
    yanlış broker kullanılması önlenir.
    """
    global _alpaca_paper_instance, _alpaca_live_instance
    global _binance_paper_instance, _binance_live_instance

    broker_name = broker_name.upper()

    if broker_name == "ALPACA":
        from services.broker.alpaca_bridge import AlpacaBroker
        if paper:
            if _alpaca_paper_instance is None:
                logger.info("[BROKER FACTORY] AlpacaBroker PAPER instance oluşturuldu.")
                _alpaca_paper_instance = AlpacaBroker(paper=True)
            return _alpaca_paper_instance
        else:
            if _alpaca_live_instance is None:
                logger.info("[BROKER FACTORY] AlpacaBroker LIVE instance oluşturuldu.")
                _alpaca_live_instance = AlpacaBroker(paper=False)
            return _alpaca_live_instance
    elif broker_name == "BINANCE":
        from services.broker.binance_bridge import BinanceBroker
        if paper:
            if _binance_paper_instance is None:
                logger.info("[BROKER FACTORY] BinanceBroker PAPER (Testnet) instance oluşturuldu.")
                _binance_paper_instance = BinanceBroker(paper=True)
            return _binance_paper_instance
        else:
            if _binance_live_instance is None:
                logger.info("[BROKER FACTORY] BinanceBroker LIVE instance oluşturuldu.")
                _binance_live_instance = BinanceBroker(paper=False)
            return _binance_live_instance
    else:
        logger.error(f"Broker {broker_name} desteklenmiyor.")
        return None
