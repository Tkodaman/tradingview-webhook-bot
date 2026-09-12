"""
Canlı Piyasa Fiyat Akışı ve Canlı Pozisyon Yöneticisi
- Başlangıç Kasa Bakiyesi: $1,000.00 (Sınırlandı ve Kesinleşti)
- Finansal Muhasebe Eşitliği: Net Kasa Değeri = Serbest Nakit + Açık Teminat + Anlık PnL - Komisyonlar
- Kesin Bütçe Limiti: Serbest Nakit Yetersizse Pozisyon Açılmaz (Maks 10 Pozisyon x $100)
- Alpaca Doğrusal Komisyon Hesabı: SEC ($0.0000278), FINRA TAF ($0.000166/share), Crypto (%0.15) ve Slippage (%0.08)
"""

import time
import random
import json
import os
from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from core.logger import logger
from services.data_ingestion.tradingview_live_client import tradingview_live_client
from services.risk_engine.market_hours import market_hours_validator
from services.engine.advanced_analytics import advanced_analytics_engine

TRT = ZoneInfo("Europe/Istanbul")

from core.database import db_manager

class ActivePosition(BaseModel):
    id: str
    symbol: str
    market: str
    side: str  # BUY / SELL
    entry_price: float
    current_price: float
    quantity: float
    nominal_value: float
    target_profit_price: float
    stop_loss_price: float
    break_even_trigger_price: float
    break_even_activated: bool = False
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    opened_at: str
    commission_fees: float = 0.0
    status: str = "OPEN"  # OPEN, CLOSED_TP, CLOSED_SL, CLOSED_MANUAL

class LiveTradeManager:
    def __init__(self):
        self.initial_capital: float = 1000.00       # $1,000.00 Taban Sermaye
        self.realized_pnl: float = 0.0               # Gerçekleşen Toplam Net Kâr/Zarar
        self.total_commissions_paid: float = 0.0    # Ödenen Toplam Komisyon ve Kesintiler
        self.positions: Dict[str, ActivePosition] = {}
        self.trade_history: List[Dict[str, Any]] = []
        self.daily_stats: Dict[str, Dict[str, float]] = {} # Günlük İstatistikler
        self.is_macro_standby: bool = False
        self.macro_standby_reason: str = ""
        self.is_paused: bool = False
        self.pause_reason: str = ""
        self.auto_resume_reconciler: bool = True

        # Canlı Fiyat Havuzu
        self.market_prices: Dict[str, Dict[str, Any]] = {
            "NVDA": {"price": 218.93, "change_pct": -0.84, "high": 220.78, "low": 215.10, "market": "NASDAQ"},
            "QQQ": {"price": 482.50, "change_pct": 1.12, "high": 484.20, "low": 480.00, "market": "NASDAQ"},
            "AAPL": {"price": 224.20, "change_pct": 0.85, "high": 225.50, "low": 222.80, "market": "NASDAQ"},
            "MSFT": {"price": 448.50, "change_pct": 1.34, "high": 451.00, "low": 446.20, "market": "NASDAQ"},
            "META": {"price": 514.00, "change_pct": 2.80, "high": 518.20, "low": 509.00, "market": "NASDAQ"},
            "TSLA": {"price": 215.80, "change_pct": -1.15, "high": 220.40, "low": 214.50, "market": "NASDAQ"},
            "THYAO": {"price": 312.50, "change_pct": 1.80, "high": 315.00, "low": 308.50, "market": "BIST"},
            "ASELS": {"price": 64.80, "change_pct": 2.20, "high": 65.40, "low": 63.50, "market": "BIST"},
            "BTCUSDT": {"price": 65420.00, "change_pct": 3.10, "high": 66200.00, "low": 64800.00, "market": "CRYPTO"}
        }

        self.load_state()
        self.sync_with_broker()

    def sync_with_broker(self):
        from services.broker.alpaca_client import alpaca_client
        import time
        from datetime import datetime, timezone
        
        try:
            broker_positions = alpaca_client.sync_open_positions()
            if not broker_positions:
                return

            for bp in broker_positions:
                sym = bp.get("symbol")
                qty = abs(float(bp.get("qty", 0)))
                if qty == 0: continue
                
                # If we don't have it locally, add it
                if sym not in self.positions:
                    entry_price = float(bp.get("avg_entry_price", 0))
                    current_price = float(bp.get("current_price", entry_price))
                    side = "BUY" if float(bp.get("qty", 0)) > 0 else "SELL"
                    
                    # Estimate limits since broker might not return bracket details easily via /positions
                    tp_price = entry_price * 1.05 if side == "BUY" else entry_price * 0.95
                    sl_price = entry_price * 0.98 if side == "BUY" else entry_price * 1.02
                    
                    pos = ActivePosition(
                        id=f"sync_{int(time.time())}_{sym}",
                        symbol=sym,
                        market="NASDAQ",  # Defaulting to NASDAQ for Alpaca stocks
                        side=side,
                        entry_price=entry_price,
                        current_price=current_price,
                        quantity=qty,
                        nominal_value=entry_price * qty,
                        target_profit_price=tp_price,
                        stop_loss_price=sl_price,
                        break_even_trigger_price=entry_price * 1.02 if side == "BUY" else entry_price * 0.98,
                        opened_at=datetime.now(timezone.utc).isoformat(),
                        unrealized_pnl=float(bp.get("unrealized_pl", 0)),
                        unrealized_pnl_pct=float(bp.get("unrealized_plpc", 0)) * 100
                    )
                    self.positions[sym] = pos
            
            # Save the synced state to local db
            self.save_state()
        except Exception as e:
            from core.logger import logger
            logger.error(f"Failed to sync with broker: {e}")

    def load_state(self):
        try:
            data = db_manager.get_store("wallet_state")
            if data:
                self.initial_capital = data.get("initial_capital", 1000.00)
                self.realized_pnl = data.get("realized_pnl", 0.0)
                self.total_commissions_paid = data.get("total_commissions_paid", 0.0)
                self.daily_stats = data.get("daily_stats", {})
                
                pos_data = data.get("positions", {})
                for pid, pdict in pos_data.items():
                    self.positions[pid] = ActivePosition(**pdict)
            
            # Trade history is managed in DB separately but cached for API usage (last 100)
            self.trade_history = db_manager.get_all_trade_history()
        except Exception as e:
            from core.logger import logger
            logger.error(f"State load error: {e}")

    def save_state(self):
        try:
            db_manager.set_store("wallet_state", {
                "initial_capital": self.initial_capital,
                "realized_pnl": self.realized_pnl,
                "total_commissions_paid": self.total_commissions_paid,
                "daily_stats": self.daily_stats,
                "positions": {pid: p.dict() for pid, p in self.positions.items()}
            })
        except Exception as e:
            from core.logger import logger
            logger.error(f"State save error: {e}")

    def reset_account(self):
        """Hesap Bakiyesini Kesin Olarak $1,000.00 Tabanına Sıfırlama Metodu"""
        self.initial_capital = 1000.00
        self.realized_pnl = 0.0
        self.total_commissions_paid = 0.0
        self.positions.clear()
        self.trade_history.clear()
        db_manager.delete_all()
        self.save_state()

    @property
    def allocated_margin(self) -> float:
        """Açık pozisyonlardaki teminat toplamı"""
        return round(sum(p.nominal_value for p in self.positions.values() if p.status == "OPEN"), 2)

    @property
    def total_unrealized_pnl(self) -> float:
        """Açık pozisyonların anlık net PnL toplamı"""
        return round(sum(p.unrealized_pnl for p in self.positions.values() if p.status == "OPEN"), 2)

    @property
    def available_cash(self) -> float:
        """Kasadaki kullanılabilir serbest nakit tutarı"""
        return round(max(0.0, self.initial_capital + self.realized_pnl - self.allocated_margin), 2)

    @property
    def total_account_equity(self) -> float:
        """NET KASA PORTFÖY DEĞERİ (Net Equity = Nakit + Teminat + Anlık PnL)"""
        return round(self.initial_capital + self.realized_pnl + self.total_unrealized_pnl, 2)

    @property
    def account_balance(self) -> float:
        """Geriye dönük uyumluluk için Net Kasa Değeri"""
        return self.total_account_equity

    def calculate_alpaca_commission(self, symbol: str, market: str, entry_price: float, exit_price: float, quantity: float, nominal_value: float) -> Dict[str, float]:
        """
        Alpaca Markets Doğrusal Komisyon ve Yasal Ücret (SEC + FINRA TAF + Slippage) Modeli
        """
        notional_entry = nominal_value
        notional_exit = quantity * exit_price
        
        if market == "CRYPTO":
            buy_comm = round(notional_entry * 0.0015, 4)
            sell_comm = round(notional_exit * 0.0015, 4)
            sec_fee = 0.0
            finra_fee = 0.0
        else:
            buy_comm = 0.0
            sell_comm = 0.0
            sec_fee = round(notional_exit * 0.0000278, 4)
            finra_fee = round(min(8.30, max(0.01, quantity * 0.000166)), 4)

        slippage_cost = round((notional_entry + notional_exit) * 0.0008, 4)
        total_comm = round(buy_comm + sell_comm + sec_fee + finra_fee + slippage_cost, 2)
        
        return {
            "buy_comm": buy_comm,
            "sell_comm": sell_comm,
            "sec_fee": sec_fee,
            "finra_fee": finra_fee,
            "slippage_cost": slippage_cost,
            "total_commission": max(0.05, total_comm)
        }

    def get_dynamic_position_capital(self, symbol: str) -> float:
        """
        Kasa Bakiyesine Göre Dinamik Pozisyon Bütçesi (%10 Taban = ) + Süpervizör Risk Çarpanı
        """
        try:
            from services.engine.supervisor_agent import supervisor_agent
            multiplier = supervisor_agent.calculate_dynamic_budget_multiplier(self.market_prices)
        except ImportError:
            multiplier = 1.0
            
        base_capital = round(self.total_account_equity * 0.10, 2)
        adjusted_capital = base_capital * multiplier
        
        # En az 10$, en fazla bakiyenin %25'i kadar
        return max(10.0, min(adjusted_capital, self.total_account_equity * 0.25))



    def get_live_prices(self) -> Dict[str, Any]:
        """
        TradingView resmi scanner sunucularından anlık gerçek piyasa fiyatlarını çeker.
        """
        tv_live = tradingview_live_client.fetch_live_market_data()
        for sym, tv_data in tv_live.items():
            if sym not in self.market_prices:
                self.market_prices[sym] = {
                    "price": tv_data.get("price", 0.0),
                    "change_pct": tv_data.get("change_pct", 0.0),
                    "high": tv_data.get("high", 0.0),
                    "low": tv_data.get("low", 0.0),
                    "market": tv_data.get("market", "UNKNOWN"),
                    "last_updated_ts": time.time()
                }
            else:
                self.market_prices[sym]["price"] = tv_data["price"]
                self.market_prices[sym]["change_pct"] = tv_data["change_pct"]
                self.market_prices[sym]["high"] = tv_data["high"]
                self.market_prices[sym]["low"] = tv_data["low"]
                self.market_prices[sym]["market"] = tv_data.get("market", self.market_prices[sym].get("market", "UNKNOWN"))
                self.market_prices[sym]["last_updated_ts"] = time.time()

        # Makro Foresight Kontrolü
        macro_eval = advanced_analytics_engine.check_macro_correction_risk(self.market_prices)
        self.is_macro_standby = macro_eval.get("is_standby_required", False)
        self.macro_standby_reason = macro_eval.get("message", "")

        updated_data = {}
        for sym, data in self.market_prices.items():
            is_open, _, _ = market_hours_validator.is_market_open(sym)
            has_active_pos = any(p.status == "OPEN" and p.symbol.upper() == sym for p in self.positions.values())
            updated_data[sym] = {
                "symbol": sym,
                "price": data["price"],
                "change_pct": data["change_pct"],
                "high": data["high"],
                "low": data["low"],
                "market": data["market"],
                "is_open": is_open,
                "has_active_position": has_active_pos,
                "source": "TRADINGVIEW_REALTIME_FEED",
                "last_update": datetime.now(TRT).strftime("%H:%M:%S")
            }

        # Açık pozisyonların PnL ve Başa Baş (Break-Even) kontrolü
        self._evaluate_open_positions()

        return {
            "timestamp": datetime.now(TRT).strftime("%Y-%m-%d %H:%M:%S UTC+3"),
            "account_balance": self.total_account_equity,
            "cash_balance": self.available_cash,
            "allocated_margin": self.allocated_margin,
            "realized_pnl": self.realized_pnl,
            "open_positions_count": len([p for p in self.positions.values() if p.status == "OPEN"]),
            "market_ticks": updated_data,
            "is_macro_standby": self.is_macro_standby,
            "macro_standby_reason": self.macro_standby_reason
        }

    def open_position(self, symbol: str, capital: Optional[float] = None, side: str = "BUY", tp_pct: float = 3.0, sl_pct: float = 1.5, entry_price_override: Optional[float] = None) -> Optional[ActivePosition]:
        # MAKRO FORESIGHT KORUMASI: Serbest bakiyeyi güvende tut.
        if self.is_macro_standby:
            from core.logger import logger
            logger.warning(f"MAKRO KORUMA AKTİF: İşlem reddedildi ({symbol}). {self.macro_standby_reason}")
            return None

        sym = symbol.upper()
        if entry_price_override and entry_price_override > 0:
            curr_price = entry_price_override
        else:
            curr_price = self.market_prices.get(sym, {}).get("price", 100.0)
        market = self.market_prices.get(sym, {}).get("market", "NASDAQ")

        if capital is None or capital <= 0 or capital > self.available_cash:
            capital = self.get_dynamic_position_capital(sym)

        open_count = len([p for p in self.positions.values() if p.status == "OPEN"])
        if open_count >= 15 or self.available_cash < 10.0:
            return None

        # %0.08 Slippage ile gerçek giriş fiyatı
        slip_rate = 0.0008
        raw_entry = curr_price * (1.0 + slip_rate) if side == "BUY" else curr_price * (1.0 - slip_rate)
        decimals = 2 if raw_entry >= 1.0 else 6
        entry_price = round(raw_entry, decimals)
        qty = round(capital / entry_price, 4)

        if side == "BUY":
            tp_price = round(entry_price * (1.0 + (tp_pct / 100.0)), decimals)
            sl_price = round(entry_price * (1.0 - (sl_pct / 100.0)), decimals)
            be_trigger = round(entry_price * 1.010, decimals)
        else:
            tp_price = round(entry_price * (1.0 - (tp_pct / 100.0)), decimals)
            sl_price = round(entry_price * (1.0 + (sl_pct / 100.0)), decimals)
            be_trigger = round(entry_price * 0.990, decimals)

        pos_id = f"POS-{sym}-{int(time.time())}"
        pos = ActivePosition(
            id=pos_id,
            symbol=sym,
            market=market,
            side=side,
            entry_price=entry_price,
            current_price=entry_price,
            quantity=qty,
            nominal_value=capital,
            target_profit_price=tp_price,
            stop_loss_price=sl_price,
            break_even_trigger_price=be_trigger,
            opened_at=datetime.now(TRT).strftime("%H:%M:%S")
        )

        # ✔ ALPACA BROKER-SIDE BRACKET ORDER (AlpacaBroker — düzeltilmiş köprü)
        # Hata durumunda pozisyon yine de yerel olarak takip edilir (fiyat aynıyı göstermeye devam eder)
        if market in ["NASDAQ", "CRYPTO"]:
            try:
                from services.broker.factory import get_broker
                from core.config import settings
                is_paper = settings.trading_mode.upper() != "LIVE"
                broker = get_broker("ALPACA", paper=is_paper)
                if broker and broker.api:
                    res = broker.place_bracket_order(
                        symbol=sym,
                        side=side,
                        qty=qty,
                        take_profit_price=tp_price,
                        stop_loss_price=sl_price
                    )
                    if res.get("status") == "success":
                        logger.info(f"[ALPACA BRACKET] {sym} emir başarıyla iletildi. OrderID: {res.get('order_id')}")
                    else:
                        logger.warning(f"[ALPACA WARN] {sym} emir yanıtı: {res.get('message', '?')} — Pozisyon yerel olarak kaydediliyor.")
            except Exception as e:
                logger.warning(f"[ALPACA HATA] {sym} broker iletimi başarısız: {e} — Yerel pozisyon devam ediyor.")

        self.positions[pos_id] = pos
        self.save_state()
        return pos

    def close_position(self, pos_id: str, reason: str = "MANUAL_CLOSE") -> Optional[Dict[str, Any]]:
        if pos_id not in self.positions:
            return None
        pos = self.positions[pos_id]
        if pos.status != "OPEN":
            return None

        curr_price = self.market_prices.get(pos.symbol, {}).get("price", pos.current_price)
        if pos.side == "BUY":
            gross_pnl = round(pos.quantity * (curr_price - pos.entry_price), 2)
        else:
            gross_pnl = round(pos.quantity * (pos.entry_price - curr_price), 2)

        # 🚨 ALPACA BROKER-SIDE LIQUIDATION 🚨
        # Eğer yerel olarak pozisyon kapatılıyorsa (TP/SL, Trailing Stop, Manual), Alpaca'da da kapat!
        if pos.market in ["NASDAQ", "CRYPTO"]:
            try:
                from services.broker.factory import get_broker
                from core.config import settings
                is_paper = settings.trading_mode.upper() != "LIVE"
                broker = get_broker("ALPACA", paper=is_paper)
                if broker and broker.api:
                    # Liquidation cancels attached bracket orders automatically in Alpaca
                    close_res = broker.close_position(pos.symbol)
                    from core.logger import logger
                    if close_res.get("status") == "success":
                        logger.info(f"[ALPACA SYNC] {pos.symbol} pozisyonu başarıyla kapatıldı (Neden: {reason}).")
                    else:
                        logger.warning(f"[ALPACA SYNC WARN] {pos.symbol} kapatılamadı (Zaten kapanmış olabilir): {close_res.get('message')}")
            except Exception as e:
                from core.logger import logger
                logger.warning(f"[ALPACA SYNC HATA] {pos.symbol} Alpaca kapatma hatası: {e}")

        # Alpaca Doğrusal Komisyon
        comm_details = self.calculate_alpaca_commission(pos.symbol, pos.market, pos.entry_price, curr_price, pos.quantity, pos.nominal_value)
        total_comm = comm_details["total_commission"]
        net_pnl = round(gross_pnl - total_comm, 2)

        pos.status = reason
        pos.unrealized_pnl = net_pnl
        pos.commission_fees = total_comm
        
        # Kesinleşmiş Gerçekleşen Net PnL Güncellemesi
        self.realized_pnl = round(self.realized_pnl + net_pnl, 2)
        self.total_commissions_paid = round(self.total_commissions_paid + total_comm, 2)

        # Günlük istatistiklere ekle
        today = datetime.now(TRT).strftime("%Y-%m-%d")
        if today not in self.daily_stats:
            self.daily_stats[today] = {"net_pnl": 0.0, "commissions": 0.0, "trades": 0}
        
        self.daily_stats[today]["net_pnl"] = round(self.daily_stats[today]["net_pnl"] + net_pnl, 2)
        self.daily_stats[today]["commissions"] = round(self.daily_stats[today]["commissions"] + total_comm, 2)
        self.daily_stats[today]["trades"] += 1

        trade_log = {
            "pos_id": pos.id,
            "symbol": pos.symbol,
            "market": pos.market,
            "side": pos.side,
            "entry_price": pos.entry_price,
            "exit_price": curr_price,
            "quantity": pos.quantity,
            "gross_pnl": gross_pnl,
            "alpaca_commission": total_comm,
            "net_pnl": net_pnl,
            "reason": reason,
            "opened_at": pos.opened_at,
            "closed_at": datetime.now(TRT).strftime("%H:%M:%S")
        }
        self.trade_history.insert(0, trade_log)
        db_manager.insert_trade_history(trade_log)
        self.save_state()

        # Y2 DÜZELTİLDİ: Öğrenme döngüsü — kapanan pozisyon deneyim hafizasına kaydediliyor
        try:
            from services.engine.experience_memory_engine import experience_memory_engine
            market_regime = "GÜÇLÜ BOĞA" if net_pnl > 0 else "ZARAR REJİM"
            experience_memory_engine.record_completed_trade(
                symbol=pos.symbol,
                action=pos.side,
                entry_price=pos.entry_price,
                exit_price=curr_price,
                pnl_pct=round((net_pnl / pos.nominal_value) * 100.0, 2),
                market_regime=market_regime,
                indicators={"market": pos.market, "reason": reason}
            )
        except Exception as me:
            from core.logger import logger
            logger.warning(f"[MEMORY WARN] Deneyim hafizası güncelleme hatası: {me}")

        return trade_log

    def _evaluate_open_positions(self):
        for pos_id, pos in list(self.positions.items()):
            if pos.status != "OPEN":
                continue

            curr_price = self.market_prices.get(pos.symbol, {}).get("price", pos.current_price)
            last_ts = self.market_prices.get(pos.symbol, {}).get("last_updated_ts", None)

            # STALENESS KORUMASI: last_updated_ts varsa ve 90 saniyeden eskiyse bekle.
            # last_updated_ts yoksa (statik fiyat) doğrudan devam et.
            if last_ts is not None and (time.time() - last_ts) > 90:
                logger.debug(f"[STALE PRICE] {pos.symbol} fiyat verisi eskidi ({int(time.time()-last_ts)}s) — değlendirme atlandı.")
                continue

            # API Hatalarına Karşı Güvenlik Kalkanı: Fiyat 0 veya negatifse işlem yapma!
            if curr_price <= 0.0:
                continue

            pos.current_price = curr_price

            if pos.side == "BUY":
                gross = (curr_price - pos.entry_price) * pos.quantity
                pct = ((curr_price - pos.entry_price) / pos.entry_price) * 100.0

                # 1. Başa Baş (Break-Even) Kontrolü (+%1.00 kârda)
                if not pos.break_even_activated and curr_price >= pos.break_even_trigger_price:
                    pos.break_even_activated = True
                    pos.stop_loss_price = round(pos.entry_price * 1.002, 2)

                # 2. TP Kontrolü (+%3.0)
                if curr_price >= pos.target_profit_price:
                    self.close_position(pos_id, "CLOSED_TP")
                    continue

                # 3. SL Kontrolü
                if curr_price <= pos.stop_loss_price:
                    self.close_position(pos_id, "CLOSED_SL")
                    continue
            else:
                gross = (pos.entry_price - curr_price) * pos.quantity
                pct = ((pos.entry_price - curr_price) / pos.entry_price) * 100.0

                if not pos.break_even_activated and curr_price <= pos.break_even_trigger_price:
                    pos.break_even_activated = True
                    pos.stop_loss_price = round(pos.entry_price * 0.998, 2)

                if curr_price <= pos.target_profit_price:
                    self.close_position(pos_id, "CLOSED_TP")
                    continue

                if curr_price >= pos.stop_loss_price:
                    self.close_position(pos_id, "CLOSED_SL")
                    continue

            pos.unrealized_pnl = round(gross, 2)
            pos.unrealized_pnl_pct = round(pct, 2)

live_trade_manager = LiveTradeManager()
