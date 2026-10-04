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
from typing import List, Dict, Any, Optional, Union
from pydantic import BaseModel, Field
from datetime import datetime, timezone
from zoneinfo import ZoneInfo
from core.logger import logger
from services.data_ingestion.tradingview_live_client import tradingview_live_client
from services.risk_engine.market_hours import market_hours_validator
from services.engine.advanced_analytics import advanced_analytics_engine

TRT = ZoneInfo("Europe/Istanbul")

from core.database import db_manager
from core.config import settings
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
    partial_profit_taken: bool = False
    highest_price_seen: float = 0.0
    trailing_stop_activated: bool = False
    unrealized_pnl: float = 0.0
    unrealized_pnl_pct: float = 0.0
    opened_at: str
    commission_fees: float = 0.0
    status: str = "OPEN"  # OPEN, CLOSED_TP, CLOSED_SL, CLOSED_MANUAL, CLOSED_TRAILING, CLOSED_EARLY
    atr_value: float = 0.0
    use_chandelier_exit: bool = False
    capital_allocated: float = 0.0  # Pozisyon için ayrılan sermaye ($)
    broker_order_id: Optional[Union[str, int]] = None
    confidence_score: Optional[float] = None
    entry_indicators: Dict[str, Any] = Field(default_factory=dict)

class LiveTradeManager:
    def __init__(self):
        self.initial_capital: float = min(float(settings.base_portfolio_size), 5000.0)
        self.realized_pnl: float = 0.0               # Gerçekleşen Toplam Net Kâr/Zarar
        self.total_commissions_paid: float = 0.0    # Ödenen Toplam Komisyon ve Kesintiler
        self.positions: Dict[str, ActivePosition] = {}
        self.shadow_positions: Dict[str, ActivePosition] = {}
        self.trade_history: List[Dict[str, Any]] = []
        self.daily_stats: Dict[str, Dict[str, float]] = {} # Günlük İstatistikler
        self.is_macro_standby: bool = False
        self.macro_standby_reason: str = ""
        self.auto_trade_enabled: bool = False  # YZ tam otonom al-sat tetikleyicisi
        self.last_autonomous_check: float = 0.0
        self.is_paused: bool = False
        self.pause_reason: str = ""
        self.auto_resume_reconciler: bool = False

        # Canlı Fiyat Havuzu (Sıfır Sahte Veri)
        self.market_prices: Dict[str, Dict[str, Any]] = {}

        self.load_state()
        self.sync_with_broker()

    def sync_with_broker(self):
        from services.engine.ha_manager import ha_manager
        if not ha_manager.is_leader:
            self.load_state()
            return
            
        from services.broker.alpaca_client import alpaca_client
        import time
        from datetime import datetime, timezone
        from core.logger import logger
        
        try:
            broker_positions = alpaca_client.sync_open_positions()
            active_broker_symbols = set()
            if broker_positions:
                for bp in broker_positions:
                    raw_sym = bp.get("symbol")
                    asset_class = bp.get("asset_class", "us_equity")
                    qty = abs(float(bp.get("qty", 0)))
                    if qty == 0: continue
                    
                    possible_symbols = [raw_sym]
                    if asset_class == "crypto" or (raw_sym.endswith("USD") and raw_sym != "USD"):
                        logger.debug(f"[ALPACA SYNC] Ignoring crypto position {raw_sym} from Alpaca to prevent mixing with Binance.")
                        continue
                            
                    active_broker_symbols.update(possible_symbols)
                    
                    local_pos = next((p for p in self.positions.values() if p.symbol in possible_symbols and p.status == "OPEN"), None)
                    
                    if not local_pos:
                        sym = possible_symbols[-1] if (asset_class == "crypto" and len(possible_symbols) > 1) else raw_sym
                        market = "CRYPTO" if asset_class == "crypto" or raw_sym.endswith("USD") else "NASDAQ"
                        entry_price = float(bp.get("avg_entry_price", 0))
                        current_price = float(bp.get("current_price", entry_price))
                        side = "BUY" if float(bp.get("qty", 0)) > 0 else "SELL"
                        
                        if market == "CRYPTO":
                            tp_margin = 0.15
                            sl_margin = 0.10
                            be_margin = 0.05
                        else:
                            tp_margin = 0.10
                            sl_margin = 0.05
                            be_margin = 0.03
                            
                        tp_price = entry_price * (1 + tp_margin) if side == "BUY" else entry_price * (1 - tp_margin)
                        sl_price = entry_price * (1 - sl_margin) if side == "BUY" else entry_price * (1 + sl_margin)
                        be_price = entry_price * (1 + be_margin) if side == "BUY" else entry_price * (1 - be_margin)
                        
                        pos = ActivePosition(
                            id=f"sync_{int(time.time())}_{sym}",
                            symbol=sym,
                            market=market,
                            side=side,
                            entry_price=entry_price,
                            current_price=current_price,
                            quantity=qty,
                            nominal_value=entry_price * qty,
                            target_profit_price=tp_price,
                            stop_loss_price=sl_price,
                            break_even_trigger_price=be_price,
                            opened_at=datetime.now(timezone.utc).isoformat(),
                            unrealized_pnl=float(bp.get("unrealized_pl", 0)),
                            unrealized_pnl_pct=float(bp.get("unrealized_plpc", 0)) * 100
                        )
                        self.positions[pos.id] = pos
                    else:
                        real_entry_price = float(bp.get("avg_entry_price", 0))
                        if real_entry_price > 0:
                            local_pos.entry_price = real_entry_price
                            local_pos.quantity = qty
                            local_pos.nominal_value = real_entry_price * qty
            
            # Hayalet Pozisyon Temizligi (Ghost Position Cleanup)
            # PENDING_BROKER dahil: broker'da yoksa temizle
            stale_positions = [
                p for p in self.positions.values()
                if p.status in ["OPEN", "PENDING_BROKER"] and p.symbol not in active_broker_symbols
                # Kripto (Spot) pozisyonları yerel hafızada tutulur (Broker 'pozisyon' klasöründe görünmez), Hayalet sayma!
                and not ("USDT" in p.symbol or "/" in p.symbol or p.symbol.endswith("USD") or "BTC" in p.symbol)
            ]
            for sp in stale_positions:
                logger.info(f"[GHOST CLEANUP] {sp.symbol} broker'da yok (status={sp.status}). Hayalet pozisyon silindi.")
                self.close_position(sp.id, "CLOSED_OFFLINE_SYNC")
                # Hemen sil — bir daha gorunmesin
                self.positions.pop(sp.id, None)

            
            # Save the synced state to local db
            self.save_state()
        except Exception as e:
            logger.error(f"Failed to sync with broker: {e}")

    def load_state(self):
        try:
            data = db_manager.get_store("wallet_state")
            if data:
                self.initial_capital = float(settings.base_portfolio_size) # Bütçe ayardan gelir
                self.realized_pnl = data.get("realized_pnl", 0.0)
                self.total_commissions_paid = data.get("total_commissions_paid", 0.0)
                self.daily_stats = data.get("daily_stats", {})
                
                pos_data = data.get("positions", {})
                for pid, pdict in pos_data.items():
                    self.positions[pid] = ActivePosition(**pdict)
            
            # Trade history is managed in DB separately but cached for API usage (last 100)
            self.trade_history = db_manager.get_all_trade_history()

            # Otonom al-sat anahtari da kalicidir; sunucu yeniden baslasa bile korunur.
            auto_trade_data = db_manager.get_store("auto_trade_flag")
            if auto_trade_data:
                self.auto_trade_enabled = bool(auto_trade_data.get("auto_trade_enabled", False))
        except Exception as e:
            from core.logger import logger
            logger.error(f"State load error: {e}")

    def save_auto_trade_flag(self):
        try:
            db_manager.set_store("auto_trade_flag", {"auto_trade_enabled": self.auto_trade_enabled})
        except Exception as e:
            from core.logger import logger
            logger.error(f"Auto-trade flag save error: {e}")

    def save_state(self):
        from services.engine.ha_manager import ha_manager
        if not ha_manager.is_leader:
            return
            
        try:
            # KOMISYON GUVENCESI: Kaydetmeden once CLOSED_OFFLINE_SYNC ve simülasyon
            # kaynaklı komisyonlari otomatik temizle — gercek olmayan islem komisyon sayilmaz.
            COMMISSION_EXEMPT = {
                "CLOSED_OFFLINE_SYNC", "SHADOW_CLOSED", "SIMULATION_CLOSE",
                "SYNC_CLOSE", "OFFLINE_SYNC", "MANUAL_SYNC"
            }
            clean_comm = round(sum(
                float(t.get("alpaca_commission", 0.0) or 0.0)
                for t in self.trade_history
                if t.get("reason", "") not in COMMISSION_EXEMPT
            ), 2)
            # Sadece hesaplanan deger gerçekten farkliysa guncelle (gereksiz yazma engeli)
            if abs(clean_comm - self.total_commissions_paid) > 0.01:
                self.total_commissions_paid = clean_comm

            db_manager.set_store("wallet_state", {
                "initial_capital": self.initial_capital,
                "realized_pnl": self.realized_pnl,
                "total_commissions_paid": self.total_commissions_paid,
                "daily_stats": self.daily_stats,
                "positions": {pid: p.model_dump() for pid, p in self.positions.items()}
            })
        except Exception as e:
            from core.logger import logger
            logger.error(f"State save error: {e}")

    def reset_account(self):
        """Hesap Bakiyesini Alpaca'dan Çekerek Sıfırlama Metodu"""
        try:
            if settings.trading_mode in ["LIVE", "PAPER"]:
                from services.broker.factory import get_broker
                broker = get_broker(settings.active_broker, paper=(settings.trading_mode == "PAPER"))
                if broker and broker.api:
                    alpaca_equity = broker.get_account_balance()
                    if alpaca_equity > 0:
                        self.initial_capital = float(alpaca_equity)
                    else:
                        self.initial_capital = float(settings.base_portfolio_size)
                else:
                    self.initial_capital = float(settings.base_portfolio_size)
            else:
                self.initial_capital = float(settings.base_portfolio_size)
        except Exception as e:
            from core.logger import logger
            logger.error(f"Alpaca bakiye çekme hatası (Sıfırlama): {e}")
            self.initial_capital = float(settings.base_portfolio_size)
            
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
        """Kasadaki kullanılabilir serbest nakit tutarı (Alpaca'dan canlı çekilir)"""
        from core.config import settings
        if settings.trading_mode in ["PAPER", "LIVE"]:
            try:
                from services.broker.alpaca_client import alpaca_client
                return round(alpaca_client.get_available_cash(), 2)
            except Exception as e:
                from core.logger import logger
                logger.error(f"[CASH FETCH ERROR] {e}")
                
        # Fallback to local calculation
        return round(max(0.0, self.initial_capital + self.realized_pnl - self.allocated_margin), 2)

    @property
    def total_account_equity(self) -> float:
        """NET KASA PORTFÖY DEĞERİ (Alpaca'dan canlı çekilir)"""
        from core.config import settings
        if settings.trading_mode in ["PAPER", "LIVE"]:
            try:
                from services.broker.alpaca_client import alpaca_client
                return round(alpaca_client.get_account_balance(), 2)
            except Exception as e:
                from core.logger import logger
                logger.error(f"[EQUITY FETCH ERROR] {e}")
                
        # Fallback to local calculation
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
        # Kullanıcı talebi: Sadece Alpaca'nın kestiği GERÇEK borsa komisyonları sayılacak, 
        # botun kendi hesapladığı otonom/sanal "kayma (slippage)" zararı komisyona dahil edilmeyecek.
        total_comm = round(buy_comm + sell_comm + sec_fee + finra_fee, 2)
        
        return {
            "buy_comm": buy_comm,
            "sell_comm": sell_comm,
            "sec_fee": sec_fee,
            "finra_fee": finra_fee,
            "slippage_cost": slippage_cost,
            "total_commission": total_comm
        }

    def get_dynamic_position_capital(self, symbol: str, confidence_score: float = 0.5) -> float:
        """
        Kasa Bakiyesine Göre Dinamik Pozisyon Bütçesi + Süpervizör Risk Çarpanı + Kelly Kriteri
        """
        from core.config import settings
        
        sym_upper = symbol.upper()
        is_crypto = "USDT" in sym_upper or "/" in sym_upper or sym_upper.endswith("USD") or "BTC" in sym_upper
        
        if is_crypto:
            # Kullanıcı talebi: Kripto aktif bütçe 1200$, Maksimum 8 pozisyon. 
            active_budget_limit = float(settings.base_portfolio_size)
            
            allocated_crypto = sum(
                p.nominal_value for p in self.positions.values() 
                if p.status in ["OPEN", "PENDING_BROKER"] and p.market == "CRYPTO"
            )
            available = active_budget_limit - allocated_crypto
        else:
            # Alpaca (Hisse Senedi) Kesin Bütçesi: 8 Bin Dolar (12 Pozisyon)
            active_budget_limit = 8000.0
            
            allocated_stock = sum(
                p.nominal_value for p in self.positions.values()
                if p.status in ["OPEN", "PENDING_BROKER"] and p.market != "CRYPTO"
            )
            available = active_budget_limit - allocated_stock
        
        # Ortalama tahsis 1/8 (%12.5)
        # Güvene (Confidence) göre %8 ile %16 arası değişebilir.
        alloc_pct = 0.125 + (confidence_score - 0.5) * 0.10
        alloc_pct = max(0.08, min(0.16, alloc_pct))
        
        try:
            from services.engine.supervisor_agent import supervisor_agent
            multiplier = supervisor_agent.calculate_dynamic_budget_multiplier(self.market_prices)
        except ImportError:
            multiplier = 1.0
            
        base_capital = round(active_budget_limit * alloc_pct, 2)
        adjusted_capital = base_capital * multiplier
        
        # Limitler (Bir işleme kasa bütçesinin en fazla %20'si basılabilir)
        cap = max(10.0, min(adjusted_capital, active_budget_limit * 0.20)) 
        
        # Kalan serbest nakitten (available) fazla alınamaz
        return min(cap, max(10.0, available * 0.95))

    def get_live_prices(self, fetch_new: bool = True) -> Dict[str, Any]:
        """
        TradingView resmi scanner sunucularından anlık gerçek piyasa fiyatlarını çeker.
        """
        if fetch_new:
            tv_live = tradingview_live_client.fetch_live_market_data()
            for sym, tv_data in tv_live.items():
                if sym not in self.market_prices:
                    self.market_prices[sym] = {
                        "price": tv_data.get("price", 0.0),
                        "change_pct": tv_data.get("change_pct", 0.0),
                        "high": tv_data.get("high", 0.0),
                        "low": tv_data.get("low", 0.0),
                        "market": tv_data.get("market", "UNKNOWN"),
                        "last_updated_ts": tv_data.get("last_updated_ts", time.time()),
                        "source": tv_data.get("source", "UNKNOWN")
                    }
                else:
                    self.market_prices[sym]["price"] = tv_data["price"]
                    self.market_prices[sym]["change_pct"] = tv_data["change_pct"]
                    self.market_prices[sym]["high"] = tv_data["high"]
                    self.market_prices[sym]["low"] = tv_data["low"]
                    self.market_prices[sym]["market"] = tv_data.get("market", self.market_prices[sym].get("market", "UNKNOWN"))
                    self.market_prices[sym]["last_updated_ts"] = tv_data.get("last_updated_ts", time.time())
                    self.market_prices[sym]["source"] = tv_data.get("source", self.market_prices[sym].get("source", "UNKNOWN"))

            # Makro Foresight Kontrolü - Ağır İşlem, sadece yeni veri geldiğinde hesapla
            macro_eval = advanced_analytics_engine.check_macro_correction_risk(self.market_prices)
            self.is_macro_standby = macro_eval.get("is_standby_required", False)
            self.macro_standby_reason = macro_eval.get("message", "")

        updated_data = {}
        for sym, data in self.market_prices.items():
            is_open, _, _ = market_hours_validator.is_market_open(sym)
            has_active_pos = any(p.status == "OPEN" and p.symbol.upper() == sym for p in self.positions.values())
            
            price = data["price"]
            change_pct = data["change_pct"]
            high = data["high"]
            low = data["low"]
            market_type = data["market"]

            if fetch_new:
                # --- SHADOW POSITION CHECK ---
                for pid, pos in list(self.shadow_positions.items()):
                    if "SHADOW_OPEN" not in pos.status:
                        continue
                    if pos.symbol == sym:
                        curr = price
                        pos.current_price = curr
                        pnl_pct = round(((curr - pos.entry_price) / pos.entry_price) * 100.0, 2)
                        
                        is_closed = False
                        is_success = False
                        if pos.side == "BUY":
                            if curr >= pos.target_profit_price:
                                is_closed = True
                                is_success = True
                            elif curr <= pos.stop_loss_price:
                                is_closed = True
                                is_success = False
                        else: # SELL
                            if curr <= pos.target_profit_price:
                                is_closed = True
                                is_success = True
                            elif curr >= pos.stop_loss_price:
                                is_closed = True
                                is_success = False
                            
                        if is_closed:
                            pos.status = "SHADOW_CLOSED"
                            try:
                                from services.engine.trade_journal_learning import trade_journal_engine
                                opened_dt = datetime.strptime(pos.opened_at, "%Y-%m-%d %H:%M UTC")
                                duration = int((datetime.now(timezone.utc).replace(tzinfo=None) - opened_dt).total_seconds() / 60)
                                trade_journal_engine.evaluate_shadow_trade_autopsy(
                                    symbol=pos.symbol, side=pos.side, entry_price=pos.entry_price,
                                    exit_price=curr, pnl_pct=pnl_pct, duration_mins=duration, success=is_success
                                )
                            except Exception as e:
                                logger.error(f"[SHADOW EVAL ERROR] {e}")
                            del self.shadow_positions[pid]
                # -----------------------------

            updated_data[sym] = {
                "symbol": sym,
                "price": price,
                "change_pct": change_pct,
                "high": high,
                "low": low,
                "market": market_type,
                "is_open": is_open,
                "has_active_position": has_active_pos,
                "source": data.get("source", "TRADINGVIEW_REALTIME_FEED"),
                "last_update": datetime.now(TRT).strftime("%H:%M:%S"),
                "last_updated_ts": data.get("last_updated_ts"),
                "data_age_seconds": round(max(0.0, time.time() - data["last_updated_ts"]), 1) if data.get("last_updated_ts") else None
            }

        if fetch_new:
            # Açık pozisyonların PnL ve Başa Baş (Break-Even) kontrolü
            self._evaluate_open_positions()
            
            # Otonom (Auto-Trade) Alım Denetleyicisi
            if self.auto_trade_enabled:
                self._autonomous_opportunity_hunter()

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

    
    def open_shadow_position(self, symbol: str, side: str, tp_pct: float, sl_pct: float, entry_price_override: float, reason: str):
        market = market_hours_validator.get_market_type(symbol)
        
        # OTONOM ÖĞRENİM KORUMASI: Piyasa kapalıyken sahte işlem (shadow trade) açmayı reddet.
        # Böylece ML motoruna, piyasa kapalıyken yaşanan yatay ve anlamsız hareketler çöp veri olarak kaydedilmez.
        is_open, _, _ = market_hours_validator.is_market_open(symbol)
        if not is_open:
            logger.info(f"🛑 [SHADOW REJECTED] {symbol} piyasası kapalı. Çöp otonom veri birikimini önlemek için işlem reddedildi.")
            return None
            
        pos_id = f"SHADOW-{symbol}-{int(time.time())}"
        target_profit_price = round(entry_price_override * (1 + (tp_pct / 100)), 4)
        stop_loss_price = round(entry_price_override * (1 - (sl_pct / 100)), 4)

        pos = ActivePosition(
            id=pos_id,
            symbol=symbol,
            market=market,
            side=side,
            entry_price=entry_price_override,
            current_price=entry_price_override,
            quantity=0,
            nominal_value=0,
            target_profit_price=target_profit_price,
            stop_loss_price=stop_loss_price,
            break_even_trigger_price=0,
            opened_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            status=f"SHADOW_OPEN ({reason})"
        )
        self.shadow_positions[pos_id] = pos
        logger.info(f"[SHADOW TRADE] {symbol} sanal olarak işleme alındı. Neden: {reason}")
        return pos

    def open_position(self, symbol: str, capital: Optional[float] = None, side: str = "BUY", tp_pct: float = 3.0, sl_pct: float = 1.5, entry_price_override: Optional[float] = None, atr_value: float = 0.0, use_chandelier_exit: bool = True, qty_override: Optional[float] = None, status: str = "OPEN", confidence_score: Optional[float] = None, entry_indicators: Optional[Dict[str, Any]] = None, is_manual: bool = False) -> Optional[ActivePosition]:
        # MAKRO FORESIGHT KORUMASI: Serbest bakiyeyi güvende tut.
        if self.is_macro_standby and not is_manual:
            logger.warning(f"MAKRO KORUMA AKTİF: İşlem reddedildi ({symbol}). {self.macro_standby_reason}")
            return None

        sym = symbol.upper()
        # NORMALIZE SYMBOL: Prevent BATUSD vs BATUSDT duplicates
        if sym.endswith("USD") and sym != "USD":
            sym = sym + "T"
            
        if entry_price_override and entry_price_override > 0:
            curr_price = entry_price_override
        else:
            curr_price = self.market_prices.get(sym, {}).get("price", 100.0)
            
        market = self.market_prices.get(sym, {}).get("market", "NASDAQ")
        # Ensure market is set correctly for normalized cryptos
        if sym.endswith("USDT") or sym.endswith("USD"):
            market = "CRYPTO"

        if capital is None or capital <= 0 or capital > self.available_cash:
            capital = self.get_dynamic_position_capital(sym)

        # OTONOM KORUMA (ML Stop-Hunt Evader)
        try:
            from services.risk_engine.stop_hunt_evader import stop_hunt_evader
            capital, sl_pct = stop_hunt_evader.get_evasion_parameters(sym, capital, sl_pct)
        except Exception as e:
            logger.warning(f"[EVADER ERROR] {e}")

        open_count_all = len([p for p in self.positions.values() if p.status == "OPEN"])
        
        # YALITILMIŞ BÜTÇE KONTROLÜ (Binance Kripto ve Alpaca Hisse birbirine karıştırılamaz)
        from core.config import settings
        if market == "CRYPTO":
            # Binance (Kripto) Bütçesi
            max_pos = 10  # 8 Normal + 2 Yapay Zeka İnsiyatifi (Bomba Fırsatlar İçin)
            crypto_positions = [p for p in self.positions.values() if p.status in ["OPEN", "PENDING_BROKER"] and p.market == "CRYPTO"]
            open_count = len([p for p in crypto_positions if p.status == "OPEN"])
            allocated = sum(p.nominal_value for p in crypto_positions)
            available = float(settings.base_portfolio_size) - allocated
        else:
            # Alpaca (Hisse) Bütçesi: Sınır 8 Bin Dolar ve Max 12 Pozisyon
            max_pos = 12
            stock_positions = [p for p in self.positions.values() if p.status in ["OPEN", "PENDING_BROKER"] and p.market != "CRYPTO"]
            open_count = len([p for p in stock_positions if p.status == "OPEN"])
            allocated = sum(p.nominal_value for p in stock_positions)
            available = 8000.0 - allocated
        
        if open_count >= max_pos or available < 10.0 or capital > available:
            logger.warning(f"BÜTÇE LİMİTİ AŞILDI ({market} Yalıtılmış Bütçe): {sym} İşlemi reddedildi. İstenen: ${capital}, Serbest Nakit: ${available} (Açık Pozisyonlar: {open_count}/{max_pos})")
            return None

        # %0.08 Slippage ile gerçek giriş fiyatı
        slip_rate = 0.0008
        raw_entry = curr_price * (1.0 + slip_rate) if side == "BUY" else curr_price * (1.0 - slip_rate)
        decimals = 2 if raw_entry >= 1.0 else 6
        entry_price = round(raw_entry, decimals)
        
        if qty_override and qty_override > 0:
            qty = round(qty_override, 4)
            capital = round(qty * entry_price, 2)
        else:
            qty = round(capital / entry_price, 4)

        # Dinamik Başa Baş (Break-Even): TP mesafesinin %40'ında (min %0.8, maks %1.5) kilitle
        be_dist_pct = max(0.8, min(1.5, tp_pct * 0.40))
        if side == "BUY":
            tp_price = round(entry_price * (1.0 + (tp_pct / 100.0)), decimals)
            sl_price = round(entry_price * (1.0 - (sl_pct / 100.0)), decimals)
            be_trigger = round(entry_price * (1.0 + (be_dist_pct / 100.0)), decimals)
        else:
            tp_price = round(entry_price * (1.0 - (tp_pct / 100.0)), decimals)
            sl_price = round(entry_price * (1.0 + (sl_pct / 100.0)), decimals)
            be_trigger = round(entry_price * (1.0 - (be_dist_pct / 100.0)), decimals)

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
            highest_price_seen=entry_price,
            opened_at=datetime.now(timezone.utc).isoformat(),
            atr_value=atr_value,
            use_chandelier_exit=use_chandelier_exit,
            status=status,
            confidence_score=confidence_score,
            entry_indicators=entry_indicators or {}
        )

        # Broker emri: Kripto (CRYPTO) işlemleri order_router.py TWAP motoru tarafından yönetilir.
        # Hisse senetleri (NASDAQ) için Alpaca'ya lokal olarak emir iletilir.
        # Çift emir (ghost trade) önlemek için kripto broker çağrısı buradan yapılmaz.
        is_crypto_pos = ("USDT" in sym.upper() or "/" in sym or sym.upper().endswith("USD") or "BTC" in sym.upper())
        if market in ["NASDAQ"] and not is_crypto_pos:
            try:
                from services.broker.factory import get_broker
                from core.config import settings
                is_paper = settings.trading_mode.upper() != "LIVE"
                broker = get_broker("ALPACA", paper=is_paper)
                    
                if broker and getattr(broker, 'api', None):
                    res = broker.place_bracket_order(
                        symbol=sym,
                        side=side,
                        qty=qty,
                        take_profit_price=tp_price,
                        stop_loss_price=sl_price,
                        limit_price=entry_price
                    )
                    if res.get("status") == "success":
                        pos.broker_order_id = res.get("order_id")
                        pos.status = "OPEN"
                        logger.info(f"[BROKER ALPACA] {sym} emir başarıyla iletildi. OrderID: {res.get('order_id')}. Statü OPEN olarak güncellendi.")
                    else:
                        err_msg = res.get("message", "?")
                        if not is_paper:
                            logger.error(f"[ALPACA REJECTED - LIVE] {sym}: {err_msg}. Pozisyon açılmadı.")
                            return None
                        else:
                            logger.warning(f"[BROKER REJECTED - PAPER] {sym}: {err_msg}. Lokal (sanal) pozisyon açılıyor.")
                else:
                    logger.warning(f"[SIMULATION] {sym}: Alpaca API bağlantısı yok. Lokal pozisyon açılıyor.")
            except Exception as e:
                from core.config import settings
                is_paper = settings.trading_mode.upper() != "LIVE"
                if not is_paper:
                    logger.error(f"[BROKER HATA - LIVE] {sym} Alpaca iletimi başarısız: {e}. Pozisyon açılmadı.")
                    return None
                else:
                    logger.warning(f"[BROKER HATA - PAPER] {sym} Alpaca bağlantısı başarısız: {e}. Lokal pozisyon açılıyor.")
        elif is_crypto_pos:
            logger.info(f"[CRYPTO BROKER] {sym}: Broker emri order_router TWAP motoruna devredildi (Çift Emir Koruması AKTİF).")

        self.positions[pos_id] = pos
        self.save_state()
        return pos

    def _take_partial_profit(self, pos_id: str, ratio: float = 0.50):
        """
        KÂR KİLİDİ: TP mesafesinin %33'üne ulaşan pozisyonlarda %50 kısmi kâr alır,
        kalan pozisyonu Başa Baş (Break-Even) noktasına kilitleyerek cüretkar şekilde
        kalan kârı büyütmeye devam eder (sermaye asla tekrar zarara dönmez).
        """
        from services.engine.ha_manager import ha_manager
        if not ha_manager.is_leader:
            logger.warning(f"💤 [HA STANDBY] Kısmi kâr alma kararı verildi (pos_id: {pos_id}), ancak bu Node LİDER olmadığı için broker emri gönderilmiyor.")
            return

        pos = self.positions.get(pos_id)
        if not pos or pos.status != "OPEN" or pos.partial_profit_taken:
            return

        curr_price = self.market_prices.get(pos.symbol, {}).get("price", pos.current_price)
        if curr_price <= 0 or pos.quantity <= 0:
            return

        close_qty = round(pos.quantity * ratio, 4)
        if close_qty <= 0 or close_qty >= pos.quantity:
            logger.warning(f"[BUG FIX] Kısmi kâr iptal edildi. close_qty ({close_qty}) mantıksız. Mevcut qty: {pos.quantity}")
            return

        if pos.side == "BUY":
            gross_pnl = round(close_qty * (curr_price - pos.entry_price), 2)
        else:
            gross_pnl = round(close_qty * (pos.entry_price - curr_price), 2)

        is_sim = settings.trading_mode == "SIMULATION" or pos.status == "SHADOW_OPEN"
        if is_sim:
            total_comm = 0.0
        else:
            comm_details = self.calculate_alpaca_commission(pos.symbol, pos.market, pos.entry_price, curr_price, close_qty, round(close_qty * pos.entry_price, 2))
            total_comm = comm_details["total_commission"]
        net_pnl = round(gross_pnl - total_comm, 2)

        # Broker: gerçek kısmi satış emri (best-effort; hata olursa sadece lokal muhasebe güncellenir)
        if pos.market in ["NASDAQ", "CRYPTO"]:
            try:
                from services.broker.factory import get_broker
                is_paper = settings.trading_mode.upper() != "LIVE"
                target_broker_name = "BINANCE" if pos.market == "CRYPTO" else "ALPACA"
                broker = get_broker(target_broker_name, paper=is_paper if target_broker_name == "ALPACA" else True)
                
                if target_broker_name == "BINANCE" and broker and getattr(broker, 'client', None):
                    broker.place_market_order(pos.symbol, "SELL" if pos.side == "BUY" else "BUY", close_qty)
                elif target_broker_name == "ALPACA" and broker and getattr(broker, 'api', None):
                    tif = "day"
                    broker.api.submit_order(
                        symbol=broker._format_symbol(pos.symbol),
                        qty=str(close_qty),
                        side="sell" if pos.side == "BUY" else "buy",
                        type="market",
                        time_in_force=tif,
                    )
            except Exception as e:
                logger.warning(f"[KÂR KİLİDİ BROKER WARN] {pos.symbol} kısmi kâr emri iletilemedi: {e}")

        self.realized_pnl = round(self.realized_pnl + net_pnl, 2)
        self.total_commissions_paid = round(self.total_commissions_paid + total_comm, 2)
        pos.quantity = round(pos.quantity - close_qty, 4)
        pos.nominal_value = round(pos.nominal_value * (1 - ratio), 2)
        pos.partial_profit_taken = True

        # Kalan pozisyonu Başa Baş noktasına kilitle (sermaye bir daha zarara dönmesin)
        pos.break_even_activated = True
        be_price = round(pos.entry_price * 1.002, 5) if pos.side == "BUY" else round(pos.entry_price * 0.998, 5)
        moved = False
        if pos.side == "BUY" and be_price > pos.stop_loss_price:
            pos.stop_loss_price = be_price
            moved = True
        elif pos.side == "SELL" and be_price < pos.stop_loss_price:
            pos.stop_loss_price = be_price
            moved = True
        if moved:
            try:
                from services.broker.alpaca_client import alpaca_client
                alpaca_client.update_bracket_orders(pos.symbol, stop_loss_price=pos.stop_loss_price)
            except Exception:
                pass

        today = datetime.now(TRT).strftime("%Y-%m-%d")
        if today not in self.daily_stats:
            self.daily_stats[today] = {"net_pnl": 0.0, "commissions": 0.0, "trades": 0}
        self.daily_stats[today]["net_pnl"] = round(self.daily_stats[today]["net_pnl"] + net_pnl, 2)
        self.daily_stats[today]["commissions"] = round(self.daily_stats[today]["commissions"] + total_comm, 2)

        trade_log = {
            "pos_id": pos.id,
            "symbol": pos.symbol,
            "market": pos.market,
            "side": pos.side,
            "entry_price": pos.entry_price,
            "exit_price": curr_price,
            "quantity": close_qty,
            "gross_pnl": gross_pnl,
            "alpaca_commission": total_comm,
            "net_pnl": net_pnl,
            "reason": "PARTIAL_TP_LOCK",
            "opened_at": pos.opened_at,
            "closed_at": datetime.now(TRT).strftime("%Y-%m-%d %H:%M:%S")
        }
        self.trade_history.insert(0, trade_log)
        db_manager.insert_trade_history(trade_log)
        self.save_state()

        logger.info(f"💰 [KÂR KİLİDİ] {pos.symbol} TP mesafesinin %33'üne ulaştı. %{int(ratio*100)} kısmi kâr alındı (Net: ${net_pnl}). Kalan {pos.quantity} adet Başa Baş'a kilitlendi.")

    def check_and_cancel_stale_orders(self):
        """
        Alpaca'da 'askıda' (pending/open) kalan emirleri kontrol eder.
        Eğer bir limit emri 5 dakikadan uzun süredir gerçekleşmemişse iptal eder ve vazgeçer.
        Özellikle Piyasa Öncesi / Sonrası (Pre/Post Market) için çok kritiktir.
        """
        try:
            from services.broker.factory import get_broker
            from core.config import settings
            import datetime
            
            is_paper = settings.trading_mode.upper() != "LIVE"
            broker = get_broker("ALPACA", paper=is_paper)
            
            if not broker or not broker.api:
                return

            open_orders = broker.api.list_orders(status="open")
            if not open_orders:
                return

            now = datetime.datetime.now(datetime.timezone.utc)
            for order in open_orders:
                # Alpaca order.submitted_at is a datetime object
                try:
                    if hasattr(order, 'submitted_at') and order.submitted_at:
                        submitted = order.submitted_at
                        diff = (now - submitted).total_seconds() / 60.0
                        if diff >= 5.0:  # 5 dakikadan fazla askıda kaldıysa
                            logger.info(f"⏳ [STALE ORDER CANCELED] Emir 5 dakikadır dolmadı. İptal ediliyor (Vazgeçildi): {order.symbol} (Süre: {diff:.1f} dk)")
                            broker.api.cancel_order(order.id)
                            
                            # Kapanan emri hafızadan da (memory) kapat / sil
                            sym = order.symbol.replace('/', '')
                            matched_pos = None
                            for pid, p in self.positions.items():
                                if p.symbol == sym and p.status == "OPEN":
                                    matched_pos = p
                                    break
                            
                            if matched_pos:
                                self.close_position(matched_pos.id, "CANCELED_TIMEOUT")
                except Exception as e:
                    logger.warning(f"Askıda emir iptalinde hata (ID: {order.id}): {e}")

        except Exception as err:
            logger.error(f"[Stale Orders Check Error] {err}")

    def close_position(self, pos_id: str, reason: str = "MANUAL_CLOSE") -> Optional[Dict[str, Any]]:
        from services.engine.ha_manager import ha_manager
        if not ha_manager.is_leader:
            logger.warning(f"💤 [HA STANDBY] Pozisyon kapatma kararı verildi ({reason}), ancak bu Node LİDER olmadığı için işlem uygulanmıyor.")
            return None

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

        # 🚨 BROKER-SIDE LIQUIDATION 🚨
        if pos.market in ["NASDAQ", "CRYPTO"] and not pos.id.startswith("SHADOW"):
            try:
                from services.broker.factory import get_broker
                from core.config import settings
                is_paper = settings.trading_mode.upper() != "LIVE"
                
                target_broker_name = "BINANCE" if pos.market == "CRYPTO" else "ALPACA"
                broker = get_broker(target_broker_name, paper=is_paper if target_broker_name == "ALPACA" else True) # Binance is always Testnet (Paper) for now
                
                if broker and getattr(broker, 'api', None) or (target_broker_name == "BINANCE" and getattr(broker, 'client', None)):
                    # Liquidation cancels attached bracket orders automatically
                    close_res = broker.close_position(pos.symbol)
                    from core.logger import logger
                    if close_res.get("status") == "success":
                        logger.info(f"[ALPACA SYNC] {pos.symbol} pozisyonu başarıyla kapatıldı (Neden: {reason}).")
                    else:
                        logger.warning(f"[ALPACA SYNC WARN] {pos.symbol} kapatılamadı (Zaten kapanmış olabilir): {close_res.get('message')}")
                    
                    # Eğer pozisyon Alpaca'ya yansımamışsa (PENDING LIMIT durumundaysa), o askıda kalan emri bulup iptal et:
                    if target_broker_name == "ALPACA":
                        try:
                            open_orders = broker.api.list_orders(status='open')
                            formatted_sym = broker._format_symbol(pos.symbol)
                            for o in open_orders:
                                if broker._format_symbol(o.symbol) == formatted_sym:
                                    broker.api.cancel_order(o.id)
                                    logger.info(f"🗑️ [ALPACA CLEANUP] {pos.symbol} için askıda kalan açık emir ({o.id}) iptal edildi.")
                        except Exception as cancel_err:
                            logger.warning(f"[ALPACA CLEANUP WARN] {pos.symbol} açık emirleri iptal edilemedi: {cancel_err}")
                        
            except Exception as e:
                from core.logger import logger
                logger.warning(f"[ALPACA SYNC HATA] {pos.symbol} Alpaca kapatma/iptal hatası: {e}")

        # Alpaca Doğrusal Komisyon
        # KURAL: CLOSED_OFFLINE_SYNC, SHADOW veya SIMULATION kaynakli kapanislarda
        # komisyon HESAPLANMAZ — gercek Alpaca dolumu olmayan islemlere komisyon uygulanamaz.
        COMMISSION_EXEMPT_REASONS = {
            "CLOSED_OFFLINE_SYNC", "SHADOW_CLOSED", "SIMULATION_CLOSE",
            "SYNC_CLOSE", "OFFLINE_SYNC", "MANUAL_SYNC"
        }
        is_simulation_mode = getattr(__import__('core.config', fromlist=['settings']).settings, 'trading_mode', '') == 'SIMULATION'

        if reason in COMMISSION_EXEMPT_REASONS or is_simulation_mode or pos.status == "SHADOW_OPEN":
            total_comm = 0.0
            net_pnl = round(gross_pnl, 2)
        else:
            comm_details = self.calculate_alpaca_commission(pos.symbol, pos.market, pos.entry_price, curr_price, pos.quantity, pos.nominal_value)
            total_comm = comm_details["total_commission"]
            net_pnl = round(gross_pnl - total_comm, 2)


        pos.status = reason
        pos.unrealized_pnl = net_pnl
        pos.commission_fees = total_comm
        
        # 🔔 SESLİ UYARI ALARMI (10 saniye) 🔔
        if reason in ["CLOSED_TP", "CLOSED_SL", "CLOSED_TRAILING"]:
            def _play_alarm():
                try:
                    import winsound, time
                    for _ in range(10):
                        winsound.Beep(1500 if "TP" in reason else 500, 500)
                        time.sleep(0.5)
                except Exception:
                    pass
            import threading
            threading.Thread(target=_play_alarm, daemon=True).start()
            
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
            "closed_at": datetime.now(TRT).strftime("%Y-%m-%d %H:%M:%S")
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
                pnl_pct=round((net_pnl / pos.nominal_value) * 100.0, 2) if pos.nominal_value > 0 else 0.0,
                market_regime=market_regime,
                indicators={**(pos.entry_indicators or {}), "market": pos.market, "reason": reason},
                ai_confidence=pos.confidence_score,
                pnl_amount=net_pnl
            )
        except Exception as me:
            from core.logger import logger
            logger.warning(f"[MEMORY WARN] Deneyim hafizası güncelleme hatası: {me}")

        # === DEVRE KESICI: Kapanan pozisyonun sonucunu kaydet ===
        try:
            from services.risk_engine.consecutive_loss_breaker import consecutive_loss_breaker
            consecutive_loss_breaker.record_trade_result(pos.symbol, net_pnl)
        except Exception as clb_e:
            pass

        # === ML MODEL: Kapanan pozisyonun ozelliklerini egitim verisine ekle ===
        try:
            from services.trainer.ml_signal_predictor import ml_predictor
            indicators_at_close = {"market": pos.market, "reason": reason}
            ml_predictor.record_trade_result(
                symbol=pos.symbol,
                indicators=indicators_at_close,
                pnl=net_pnl,
                context={}
            )
        except Exception as ml_e:
            pass

        return trade_log

    def _autonomous_opportunity_hunter(self):
        """
        [DEVRE DIŞI] Bu motor auto_runner.py Hunter Mode v3 ile çakışıyordu.
        Otonom al-sat kararları artık yalnızca auto_runner.py tarafından verilir.
        live_stream.py sadece fiyat güncellemesi ve pozisyon yönetimi yapar.
        """
        return  # Çift motor çakışması giderildi — auto_runner.py tek avcı



    def _evaluate_open_positions(self):
        for pos_id, pos in list(self.positions.items()):
            if pos.status != "OPEN":
                continue

            # Hayalet Senkronizasyon (Ghost Position Loop) Koruması:
            # Piyasa kapalıyken yerel Stop Loss / Take Profit değerlendirmesi yapma.
            # Alpaca kapalı piyasada emri beklemeye alır, ancak yerel motor pozisyonu
            # kapatıp ML'e "ZARAR REJİM" kaydeder. Sonra sync_with_broker çalışıp
            # kapanmamış Alpaca pozisyonunu geri getirir ve bu döngü ML veritabanını çöplüğe çevirir.
            is_open = True
            try:
                from services.risk_engine.market_hours import market_hours_validator
                is_open, _, _ = market_hours_validator.is_market_open(pos.symbol)
            except Exception:
                pass

            search_sym = pos.symbol
            if search_sym not in self.market_prices and (search_sym + "T") in self.market_prices:
                search_sym = search_sym + "T"

            curr_price = self.market_prices.get(search_sym, {}).get("price", pos.current_price)
            last_ts = self.market_prices.get(search_sym, {}).get("last_updated_ts", None)

            # Fail-closed: timestamp yoksa veya fiyat 90 saniyeyi geçtiyse
            # statik veriye dayanarak yerel stop/TP kapatması yapma.
            if last_ts is None:
                logger.debug(f"[NO TIMESTAMP] {pos.symbol} için taze fiyat zamanı yok — değerlendirme atlandı.")
                continue
            if (time.time() - last_ts) > 90:
                logger.debug(f"[STALE PRICE] {pos.symbol} fiyat verisi eskidi ({int(time.time()-last_ts)}s) — değerlendirme atlandı.")
                continue

            # API Hatalarına Karşı Güvenlik Kalkanı: Fiyat 0 veya negatifse işlem yapma!
            if curr_price <= 0.0:
                continue

            # Her zaman yerel fiyatı güncelle (Kripto için zorunludur çünkü Alpaca Sync Kripto verisini beslemez)
            pos.current_price = curr_price

            if pos.side == "BUY":
                # En yüksek fiyat güncellemesi (Trailing Stop İçin)
                if curr_price > pos.highest_price_seen:
                    pos.highest_price_seen = curr_price

                gross = (curr_price - pos.entry_price) * pos.quantity
                pct = ((curr_price - pos.entry_price) / pos.entry_price) * 100.0
                
                # Arayüz (Dashboard) Dinamikliği İçin PnL'i Anlık Güncelle
                pos.unrealized_pnl = gross
                pos.unrealized_pnl_pct = pct

                # === KURUMLARIN GEMİYİ TERK ETMESİ (SMART MONEY DUMP / INSTITUTIONAL EXIT) ===
                cmf = self.market_prices.get(search_sym, {}).get("cmf")
                if cmf is not None and float(cmf) <= -0.15:
                    if is_open:
                        logger.warning(f"🚨 [SMART MONEY DUMP] {pos.symbol} için CMF {float(cmf):.3f} seviyesine çakıldı! Kurumlar boşaltıyor. Kâr/Zarar: %{pct:.2f}. ACİL ÇIKIŞ (Kaos öncesi kaçış).")
                        from services.engine.bot_thought_stream import bot_thought_stream
                        bot_thought_stream.add("🌊 SMART MONEY SÖRFÜ", pos.symbol, f"Kurumlar gemiyi terk ediyor (CMF: {float(cmf):.2f}). Biz de iniyoruz.", "WARNING")
                        self.close_position(pos_id, "CLOSED_SMART_MONEY_DUMP")
                        continue

                # === KAZAN-KAZAN: FLASH CRASH (HABER ETKİSİ) KORUMASI ===
                if pct <= -4.0 and not pos.trailing_stop_activated:
                    if is_open:
                        logger.warning(f"🚨 [FLASH CRASH DETECTED] {pos.symbol} %{pct:.2f} düştü! Acil stop tetikleniyor.")
                        self.close_position(pos_id, "CLOSED_FLASH_CRASH")
                        continue

                # === HOPIUM / DERİN ZARAR KES (REALLOCATION) ===
                try:
                    from services.engine.risk_engine import RiskEngine
                    if RiskEngine.evaluate_portfolio_reallocation(pos.entry_price, curr_price, max_drawdown_pct=0.15) == "REALLOCATE":
                        if is_open:
                            logger.error(f"💥 [HOPIUM KIRICI - REALLOCATE] {pos.symbol} ağır zararda (%{pct:.2f}). Sistem ACTIVE_TRAILING felcinden kurtulmak için işlemi acil kesiyor!")
                            self.close_position(pos_id, "CLOSED_REALLOCATE")
                            continue
                except Exception as e:
                    pass

                # AKILLI ÇIKIŞ (Erken Kâr Alma)
                # Eğer pozisyon %1.5'tan fazla kârdaysa ve momentum zayıflıyorsa (RSI aşırı şişmiş vs. veya hacim düştüyse)
                # Otonom Tarayıcı RSI verisine doğrudan erişemediğimizden fiyatın tepeden %1 düşüşüne de bakabiliriz.
                
                # İZLEYEN STOP (Rejim Matrisi - Dinamik Step-Up Trailing Stop)
                # Risk Modu x Piyasa Rejimi kombinasyonundan makas mesafesi alınır.
                try:
                    from services.engine.market_regime_engine import regime_engine as _re_engine
                    trailing_dist_raw = _re_engine.get_trailing_dist(
                        risk_mode=settings.current_risk_mode,
                        market=pos.market,
                        pct_gain=pct
                    )
                except Exception:
                    trailing_dist_raw = None

                if trailing_dist_raw is not None:
                    trailing_dist = 1.0 - trailing_dist_raw  # dist=0.05 -> 1.0-0.05=0.95

                    # İşleme girildiğinden itibaren her yükselişte anında iz sürer
                    pos.trailing_stop_activated = True
                    new_sl = round(pos.highest_price_seen * trailing_dist, 5)
                    if new_sl > pos.stop_loss_price:
                        old_sl = pos.stop_loss_price
                        pos.stop_loss_price = new_sl
                        logger.info(f"🤖 [AI-TRAILING] {pos.symbol} için Kademeli İzleyen Stop makası (Mesafe: %{round((1-trailing_dist)*100, 1)}) daraltıldı! Eski: ${old_sl} -> Yeni: ${new_sl}")
                        try:
                            from services.broker.alpaca_client import alpaca_client
                            alpaca_client.update_bracket_orders(pos.symbol, stop_loss_price=new_sl)
                        except Exception:
                            pass

                # 1. Başa Baş (Break-Even) Kontrolü (+%2.50 kârda)
                if not pos.break_even_activated and curr_price >= pos.break_even_trigger_price:
                    pos.break_even_activated = True
                    if pos.entry_price * 1.002 > pos.stop_loss_price:
                        old_sl = pos.stop_loss_price
                        pos.stop_loss_price = round(pos.entry_price * 1.002, 5)
                        logger.info(f"🛡️ [AI-RISK] {pos.symbol} kâra geçti. Başabaş (Break-Even) noktasına çekildi: ${old_sl} -> ${pos.stop_loss_price}")
                        try:
                            from services.broker.alpaca_client import alpaca_client
                            alpaca_client.update_bracket_orders(pos.symbol, stop_loss_price=pos.stop_loss_price)
                        except Exception:
                            pass

                # 1.5 KÂR KİLİDİ (Cüretkar Kısmi Kâr Alımı): TP mesafesinin %33'üne ulaşılınca %50 kısmi kâr al, kalanı BE'ye kilitle
                if is_open and not pos.partial_profit_taken:
                    tp_dist_pct = ((pos.target_profit_price - pos.entry_price) / pos.entry_price) * 100.0
                    if tp_dist_pct > 0 and (pct / tp_dist_pct) >= 0.33:
                        self._take_partial_profit(pos_id, ratio=0.50)

                # 2. TP Kontrolü (+%3.0)
                if curr_price >= pos.target_profit_price:
                    if is_open:
                        self.close_position(pos_id, "CLOSED_TP")
                        continue

                # 3. SL / Trailing Stop Kontrolü
                if curr_price <= pos.stop_loss_price:
                    if is_open:
                        reason = "CLOSED_TRAILING" if pos.trailing_stop_activated else "CLOSED_SL"
                        logger.info(f"🛑 [DYNAMIC SL HIT] {pos.symbol} Stop seviyesine (${pos.stop_loss_price:.4f}) ulaştı (Güncel: ${curr_price:.4f}, Kayıp: %{pct:.2f}). Kestirip atılıyor.")
                        self.close_position(pos_id, reason)
                        continue
            else:
                # SHORT (Açığa Satış) için Trailing Stop
                if pos.highest_price_seen == 0.0 or curr_price < pos.highest_price_seen:
                    pos.highest_price_seen = curr_price

                gross = (pos.entry_price - curr_price) * pos.quantity
                pct = ((pos.entry_price - curr_price) / pos.entry_price) * 100.0

                # === HOPIUM / DERİN ZARAR KES (REALLOCATION) ===
                try:
                    from services.engine.risk_engine import RiskEngine
                    # For short, current_price > entry_price means drawdown. evaluate_portfolio_reallocation expects (entry, current) where current < entry is drawdown.
                    # We can reverse them or write custom logic.
                    drawdown = (curr_price - pos.entry_price) / pos.entry_price
                    if drawdown >= 0.15:
                        if is_open:
                            logger.error(f"💥 [HOPIUM KIRICI - REALLOCATE SHORT] {pos.symbol} ağır zararda (%{pct:.2f}). Sistem ACTIVE_TRAILING felcinden kurtulmak için işlemi acil kesiyor!")
                            self.close_position(pos_id, "CLOSED_REALLOCATE")
                            continue
                except Exception as e:
                    pass

                is_sniper = settings.current_risk_mode.upper() == "SNIPER"
                
                orig_sl_pct = (pos.stop_loss_price - pos.entry_price) / pos.entry_price if pos.stop_loss_price > pos.entry_price else 0.03
                base_dist = 1.0 + min(orig_sl_pct, 0.02 if is_sniper else 0.03)

                if pct > 4.0:
                    trailing_dist = 1.005 # %0.5 makas!
                elif pct > 2.0:
                    trailing_dist = 1.008 # %0.8 makas!
                elif pct > 1.0:
                    trailing_dist = 1.012 # %1.2 makas!
                elif pct > 0.5:
                    trailing_dist = 1.015 # %1.5 makas
                else:
                    trailing_dist = base_dist

                pos.trailing_stop_activated = True
                new_sl = round(pos.highest_price_seen * trailing_dist, 5)
                if new_sl < pos.stop_loss_price:
                    old_sl = pos.stop_loss_price
                    pos.stop_loss_price = new_sl
                    logger.info(f"🤖 [AI-TRAILING SHORT] {pos.symbol} için İzleyen Stop daraltıldı! Eski: ${old_sl} -> Yeni: ${new_sl}")
                    try:
                        from services.broker.alpaca_client import alpaca_client
                        alpaca_client.update_bracket_orders(pos.symbol, stop_loss_price=new_sl)
                    except Exception:
                        pass

                if not pos.break_even_activated and curr_price <= pos.break_even_trigger_price:
                    pos.break_even_activated = True
                    if pos.entry_price * 0.998 < pos.stop_loss_price:
                        old_sl = pos.stop_loss_price
                        pos.stop_loss_price = round(pos.entry_price * 0.998, 5)
                        logger.info(f"🛡️ [AI-RISK SHORT] {pos.symbol} kâra geçti. Başabaş noktasına çekildi: ${old_sl} -> ${pos.stop_loss_price}")
                        try:
                            from services.broker.alpaca_client import alpaca_client
                            alpaca_client.update_bracket_orders(pos.symbol, stop_loss_price=pos.stop_loss_price)
                        except Exception:
                            pass

                # 1.5 KÂR KİLİDİ (Cüretkar Kısmi Kâr Alımı): TP mesafesinin %33'üne ulaşılınca %50 kısmi kâr al, kalanı BE'ye kilitle
                if is_open and not pos.partial_profit_taken:
                    tp_dist_pct = ((pos.entry_price - pos.target_profit_price) / pos.entry_price) * 100.0
                    if tp_dist_pct > 0 and (pct / tp_dist_pct) >= 0.33:
                        self._take_partial_profit(pos_id, ratio=0.50)

                if curr_price <= pos.target_profit_price:
                    if is_open:
                        self.close_position(pos_id, "CLOSED_TP")
                        continue

                if curr_price >= pos.stop_loss_price:
                    if is_open:
                        reason = "CLOSED_TRAILING" if pos.trailing_stop_activated else "CLOSED_SL"
                        self.close_position(pos_id, reason)
                        continue

            # CANLI KOKPİT GERÇEK ZAMANLI PNL HESABI (Tüm Modlar İçin)
            # Kullanıcı talebi: Gerçek al-sat için komisyon totalden çıkarılsın, simülasyon hesaplanmasın.
            is_sim = settings.trading_mode == "SIMULATION" or pos.status == "SHADOW_OPEN"
            est_comm = 0.0
            if not is_sim:
                comm_details = self.calculate_alpaca_commission(pos.symbol, pos.market, pos.entry_price, curr_price, pos.quantity, pos.nominal_value)
                est_comm = comm_details["total_commission"]
            
            pos.commission_fees = est_comm
            pos.unrealized_pnl = round(gross - est_comm, 2)
            pos.unrealized_pnl_pct = round((pos.unrealized_pnl / pos.nominal_value) * 100.0, 2) if pos.nominal_value > 0 else 0.0

live_trade_manager = LiveTradeManager()
