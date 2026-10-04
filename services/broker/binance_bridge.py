from typing import Dict, Any, List
import time
import math
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
            logger.error("[BINANCE] python-binance kutuphanesi yuklu degil! Testnet simülasyonu devrede.")
            self.client = None

        if not self.api_key or not self.secret_key:
            logger.warning("[BINANCE] API anahtarlari eksik, testnet simülasyonu devrede.")
            self.client = None

        if self.api_key and self.secret_key:
            try:
                # Paper mode for Binance is Testnet
                # Proxy iptal edildi (SSL EOF hatasına neden olduğu için doğrudan bağlanılacak)
                self.client = Client(self.api_key, self.secret_key, testnet=paper)
                logger.info(f"[BINANCE] Baglanti saglandi. Mod: {'PAPER (Testnet)' if paper else 'LIVE'}")
            except Exception as e:
                logger.error(f"[BINANCE] Baglanti hatasi: {e}")
                self.client = None
        
        self.is_paper = paper
        if not self.client and self.is_paper:
            logger.info("[BINANCE] Testnet baglantisi basarisiz oldugu icin KUSURSUZ SIMULASYON moduna gecildi.")


    def _format_symbol(self, symbol: str) -> str:
        # Format "WLDUSDT" from things like "BINANCE:WLDUSDT"
        sym = symbol.split(":")[-1]
        sym = sym.replace("/", "").replace("-", "")
        # Ensure it ends with USDT for typical crypto
        if not sym.endswith("USDT") and not sym.endswith("BUSD") and not sym.endswith("BTC"):
            sym = sym + "USDT"
        return sym.upper()
        
    def get_account_balance(self) -> float:
        if not self.client:
            if getattr(self, "is_paper", False):
                return float(settings.base_portfolio_size)
            return 0.0
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
        if not self.client:
            if getattr(self, "is_paper", False):
                logger.info(f"[BINANCE MOCK] {symbol} pozisyonu sanal olarak kapatildi.")
                return {"status": "success", "order_id": f"MOCK-CLOSE-{symbol}-{int(time.time())}", "details": {}}
            return {"status": "error", "message": "Client not initialized"}
        try:
            sym = self._format_symbol(symbol)
            base_asset = sym.replace("USDT", "").replace("BTC", "").replace("USD", "")
            
            # Önce bu coine ait tüm açık emirleri (Örn: OCO Stop Loss emrini) iptal et ki kilitli bakiye 'free' (boş) hale gelsin.
            try:
                open_orders = self.client.get_open_orders(symbol=sym)
                for order in open_orders:
                    self.client.cancel_order(symbol=sym, orderId=order['orderId'])
                if open_orders:
                    logger.info(f"[BINANCE CLEANUP] {sym} için {len(open_orders)} adet açık emir iptal edildi (Bakiye serbest bırakıldı).")
            except Exception as cancel_e:
                logger.warning(f"[BINANCE CLEANUP WARN] {sym} açık emirleri iptal edilemedi: {cancel_e}")
                
            # Binance'da bakiye kontrolü
            balance = self.client.get_asset_balance(asset=base_asset)
            if balance and float(balance['free']) > 0:
                free_qty = float(balance['free'])
                
                # Minimum satılabilir miktar (LOT_SIZE) ve ondalık hassasiyet (stepSize) bul
                info = self.client.get_symbol_info(sym)
                step_size = 1.0
                for f in info['filters']:
                    if f['filterType'] == 'LOT_SIZE':
                        step_size = float(f['stepSize'])
                        break
                
                # Hassasiyete göre yuvarlama
                precision = int(round(-math.log(step_size, 10), 0))
                sell_qty = round(free_qty - (free_qty % step_size), precision)
                
                if sell_qty > 0:
                    logger.info(f"[BINANCE] Kapatiliyor: {sym} | Miktar: {sell_qty}")
                    fmt_qty = f"{sell_qty:.{precision}f}" if precision > 0 else f"{int(sell_qty)}"
                    order = self.client.create_order(
                        symbol=sym,
                        side=Client.SIDE_SELL,
                        type=Client.ORDER_TYPE_MARKET,
                        quantity=fmt_qty
                    )
                    return {"status": "success", "order_id": order.get('orderId'), "details": order}
                else:
                    return {"status": "ignored", "message": "Bakiye lot size altinda."}
            else:
                return {"status": "ignored", "message": "Satilacak bakiye yok."}
        except Exception as e:
            logger.error(f"[BINANCE] Kapatma sirasinda hata {symbol}: {e}")
            return {"status": "error", "message": str(e)}

    def place_market_order(self, symbol: str, side: str, qty: float, limit_price: float = None) -> Dict[str, Any]:
        if not self.client:
            if getattr(self, "is_paper", False):
                logger.info(f"[BINANCE MOCK] Sanal Market Emri: {side} {qty} {symbol}")
                return {"status": "success", "order_id": f"MOCK-MKT-{symbol}-{int(time.time())}", "details": {}}
            return {"status": "error", "message": "Client not initialized"}
            
        sym = self._format_symbol(symbol)
        bside = Client.SIDE_BUY if side.upper() in ["BUY", "LONG"] else Client.SIDE_SELL
        
        try:
            logger.info(f"[BINANCE] Emir Gonderiliyor: {bside} {qty} {sym}")
            
            # Miktarı LOT_SIZE'a göre yuvarla
            info = self.client.get_symbol_info(sym)
            step_size = 1.0
            for f in info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    step_size = float(f['stepSize'])
                    break
            precision = int(round(-math.log(step_size, 10), 0))
            formatted_qty = round(qty - (qty % step_size), precision)
            
            if formatted_qty <= 0:
                logger.error(f"[BINANCE] Gecersiz miktar: {qty} -> {formatted_qty}")
                return {"status": "error", "message": "Formatted quantity is 0 or less"}
                
            fmt_qty = f"{formatted_qty:.{precision}f}" if precision > 0 else f"{int(formatted_qty)}"
            
            # Basit piyasa emri
            order = self.client.create_order(
                symbol=sym,
                side=bside,
                type=Client.ORDER_TYPE_MARKET,
                quantity=fmt_qty
            )
            logger.info(f"[BINANCE] Emir Basarili: {order.get('orderId')}")
            return {"status": "success", "order_id": order.get('orderId'), "details": order}
        except Exception as e:
            logger.error(f"[BINANCE] Emir basarisiz {sym}: {e}")
            return {"status": "error", "message": str(e)}
            
    def place_bracket_order(self, symbol: str, side: str, qty: float, take_profit_price: float, stop_loss_price: float, limit_price: float = None) -> Dict[str, Any]:
        # Binance Spot Bracket order OCO ile yapilir, baslangic icin basit market ile giriyoruz, OCO ile hedef setliyoruz
        if not self.client:
            if getattr(self, "is_paper", False):
                logger.info(f"[BINANCE MOCK BRACKET] Sanal Bracket Emri: {side} {qty} {symbol} | TP: {take_profit_price} SL: {stop_loss_price}")
                return {"status": "success", "order_id": f"MOCK-BRK-{symbol}-{int(time.time())}", "details": {}}
            return {"status": "error", "message": "Client not initialized"}
            
        sym = self._format_symbol(symbol)
        bside = Client.SIDE_BUY if side.upper() in ["BUY", "LONG"] else Client.SIDE_SELL
        
        try:
            logger.info(f"[BINANCE BRACKET] Giris yapiliyor: {sym}")
            
            # Miktarı LOT_SIZE'a göre yuvarla
            info = self.client.get_symbol_info(sym)
            step_size = 1.0
            for f in info['filters']:
                if f['filterType'] == 'LOT_SIZE':
                    step_size = float(f['stepSize'])
                    break
            precision = int(round(-math.log(step_size, 10), 0))
            formatted_qty = round(qty - (qty % step_size), precision)
            
            if formatted_qty <= 0:
                logger.error(f"[BINANCE BRACKET] Gecersiz miktar: {qty} -> {formatted_qty}")
                return {"status": "error", "message": "Formatted quantity is 0 or less"}
                
            fmt_qty = f"{formatted_qty:.{precision}f}" if precision > 0 else f"{int(formatted_qty)}"
                
            entry_order = self.client.create_order(
                symbol=sym,
                side=bside,
                type=Client.ORDER_TYPE_MARKET,
                quantity=fmt_qty
            )
            
            # Borsalardaki ani kopmalara karşı "Donanımsal Stop" (Hardware OCO)
            try:
                tick_size = 0.01
                for f in info['filters']:
                    if f['filterType'] == 'PRICE_FILTER':
                        tick_size = float(f['tickSize'])
                        break
                
                price_precision = 0
                if tick_size < 1.0:
                    price_precision = int(round(-math.log(tick_size, 10), 0))
                
                fmt_tp = f"{round(take_profit_price, price_precision):.{price_precision}f}"
                fmt_sl = f"{round(stop_loss_price, price_precision):.{price_precision}f}"
                
                oco_side = "SELL" if bside == "BUY" else "BUY"
                
                oco_order = self.client.create_oco_order(
                    symbol=sym,
                    side=oco_side,
                    quantity=fmt_qty,
                    price=fmt_tp,
                    stopPrice=fmt_sl,
                    stopLimitPrice=fmt_sl,
                    stopLimitTimeInForce='GTC'
                )
                logger.info(f"[BINANCE BRACKET] OCO Emri başarıyla borsaya iletildi (Donanımsal Stop Güvencesi AKTİF). TP: {fmt_tp}, SL: {fmt_sl}")
            except Exception as oco_e:
                logger.warning(f"[BINANCE BRACKET] OCO emri iletilemedi, lokal stop takibi devrede. Detay: {oco_e}")

            return {"status": "success", "order_id": entry_order.get('orderId'), "details": entry_order}
            
        except Exception as e:
            logger.error(f"[BINANCE BRACKET] Hata: {sym} - {e}")
            return {"status": "error", "message": str(e)}

    def update_bracket_orders(self, symbol: str, take_profit_price: float = None, stop_loss_price: float = None) -> Dict[str, Any]:
        if not self.client:
            return {"status": "error", "message": "Client not initialized"}
        
        sym = self._format_symbol(symbol)
        try:
            # Get open orders to find the qty and side
            open_orders = self.client.get_open_orders(symbol=sym)
            if not open_orders:
                return {"status": "error", "message": "No open orders found to update"}
                
            qty = 0.0
            side = None
            # Find the stop loss or take profit order to get quantity
            for order in open_orders:
                if order.get('type') in ['STOP_LOSS_LIMIT', 'LIMIT_MAKER']:
                    qty = float(order.get('origQty', 0))
                    side = order.get('side')
                    break
                    
            if qty == 0.0 or not side:
                return {"status": "error", "message": "Could not determine order quantity or side"}
                
            # Cancel existing open orders (the old OCO)
            for order in open_orders:
                self.client.cancel_order(symbol=sym, orderId=order['orderId'])
                
            # Format new prices
            info = self.client.get_symbol_info(sym)
            tick_size = 0.01
            step_size = 1.0
            for f in info['filters']:
                if f['filterType'] == 'PRICE_FILTER':
                    tick_size = float(f['tickSize'])
                elif f['filterType'] == 'LOT_SIZE':
                    step_size = float(f['stepSize'])
            
            price_precision = 0
            if tick_size < 1.0:
                price_precision = int(round(-math.log(tick_size, 10), 0))
                
            qty_precision = 0
            if step_size < 1.0:
                qty_precision = int(round(-math.log(step_size, 10), 0))
                
            fmt_tp = f"{round(take_profit_price, price_precision):.{price_precision}f}"
            fmt_sl = f"{round(stop_loss_price, price_precision):.{price_precision}f}"
            fmt_qty = f"{round(qty - (qty % step_size), qty_precision):.{qty_precision}f}" if qty_precision > 0 else f"{int(qty)}"

            oco_order = self.client.create_oco_order(
                symbol=sym,
                side=side,
                quantity=fmt_qty,
                price=fmt_tp,
                stopPrice=fmt_sl,
                stopLimitPrice=fmt_sl,
                stopLimitTimeInForce='GTC'
            )
            logger.info(f"[BINANCE BRACKET UPDATE] OCO Emri başarıyla güncellendi. Yeni TP: {fmt_tp}, Yeni SL: {fmt_sl}")
            return {"status": "success", "details": oco_order}
            
        except Exception as e:
            logger.error(f"[BINANCE BRACKET UPDATE ERROR] {sym}: {e}")
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
