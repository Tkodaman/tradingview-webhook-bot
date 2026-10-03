from typing import Dict, Any, List
import time
from core.logger import logger
from core.config import settings
from services.broker.base import BaseBroker

try:
    from binance.client import Client
    from binance.exceptions import BinanceAPIException
except ImportError:
    Client = None
    BinanceAPIException = Exception

class BinanceBroker(BaseBroker):
    def __init__(self, paper: bool = False):
        super().__init__()
        self.api_key = settings.binance_api_key
        self.secret_key = settings.binance_secret_key
        
        if not Client:
            logger.error("[BINANCE] python-binance kutuphanesi yuklu degil!")
            self.client = None
            return
            
        if not self.api_key or not self.secret_key:
            logger.warning("[BINANCE] API anahtarlari eksik, baglanti kurulamadi.")
            self.client = None
            return
            
        try:
            req_params = {}
            if getattr(settings, "outbound_proxy", None):
                proxy_url = settings.outbound_proxy
                req_params["proxies"] = {"http": proxy_url, "https": proxy_url}
                logger.info(f"[BINANCE] Proxy kullaniliyor: {proxy_url}")
                
            # Paper mode for Binance is Testnet
            self.client = Client(self.api_key, self.secret_key, testnet=paper, requests_params=req_params)
            logger.info(f"[BINANCE] Baglanti saglandi. Mod: {'PAPER (Testnet)' if paper else 'LIVE'}")
        except Exception as e:
            logger.error(f"[BINANCE] Baglanti hatasi: {e}")
            self.client = None

    def _format_symbol(self, symbol: str) -> str:
        # Format "WLDUSDT" from things like "BINANCE:WLDUSDT"
        sym = symbol.split(":")[-1]
        sym = sym.replace("/", "").replace("-", "")
        # Ensure it ends with USDT for typical crypto
        if not sym.endswith("USDT") and not sym.endswith("BUSD") and not sym.endswith("BTC"):
            sym = sym + "USDT"
        return sym.upper()
        
    def get_account_balance(self) -> float:
        if not self.client: return 0.0
        try:
            acc = self.client.get_account()
            for bal in acc.get('balances', []):
                if bal['asset'] == 'USDT':
                    return float(bal['free'])
            return 0.0
        except:
            return 0.0
            
    def get_cash_balance(self) -> float:
        return self.get_account_balance()

    def get_open_positions(self) -> list:
        # Spot hesapta 'pozisyon' klasigi yoktur, elde tutulan varliklardir.
        return []

    def close_position(self, symbol: str) -> Dict[str, Any]:
        # TODO: Cikis mantigi (Spot: Hepsini sat)
        logger.info(f"[BINANCE] Kapatiliyor: {symbol}")
        return {"status": "success", "message": "Not implemented yet"}

    def place_market_order(self, symbol: str, side: str, qty: float, limit_price: float = None) -> Dict[str, Any]:
        if not self.client:
            return {"status": "error", "message": "Client not initialized"}
            
        sym = self._format_symbol(symbol)
        bside = Client.SIDE_BUY if side.upper() in ["BUY", "LONG"] else Client.SIDE_SELL
        
        try:
            logger.info(f"[BINANCE] Emir Gonderiliyor: {bside} {qty} {sym}")
            # Basit piyasa emri
            order = self.client.create_order(
                symbol=sym,
                side=bside,
                type=Client.ORDER_TYPE_MARKET,
                quantity=qty
            )
            logger.info(f"[BINANCE] Emir Basarili: {order.get('orderId')}")
            return {"status": "success", "order_id": order.get('orderId'), "details": order}
        except Exception as e:
            logger.error(f"[BINANCE] Emir basarisiz {sym}: {e}")
            return {"status": "error", "message": str(e)}
            
    def place_bracket_order(self, symbol: str, side: str, qty: float, take_profit_price: float, stop_loss_price: float, limit_price: float = None) -> Dict[str, Any]:
        # Binance Spot Bracket order OCO ile yapilir, baslangic icin basit market ile giriyoruz, OCO ile hedef setliyoruz
        if not self.client:
            return {"status": "error", "message": "Client not initialized"}
            
        sym = self._format_symbol(symbol)
        bside = Client.SIDE_BUY if side.upper() in ["BUY", "LONG"] else Client.SIDE_SELL
        
        try:
            logger.info(f"[BINANCE BRACKET] Giris yapiliyor: {sym}")
            entry_order = self.client.create_order(
                symbol=sym,
                side=bside,
                type=Client.ORDER_TYPE_MARKET,
                quantity=qty
            )
            
            # TODO: OCO emri ile TP ve SL ekle (Binance API destegi gerektirir)
            # Simdilik Order Router tarafindaki local stop takibi devreye girecek
            logger.info(f"[BINANCE BRACKET] SPOT Market basarili. TP ve SL lokal olarak takip edilecek.")
            return {"status": "success", "order_id": entry_order.get('orderId'), "details": entry_order}
            
        except Exception as e:
            logger.error(f"[BINANCE BRACKET] Hata: {sym} - {e}")
            return {"status": "error", "message": str(e)}
            
    def get_realtime_prices(self, symbols: List[str]) -> Dict[str, float]:
        if not self.client:
            return {}
        try:
            res = {}
            for s in symbols:
                sym = self._format_symbol(s)
                ticker = self.client.get_symbol_ticker(symbol=sym)
                res[sym] = {"price": float(ticker['price'])}
            return res
        except Exception:
            return {}
