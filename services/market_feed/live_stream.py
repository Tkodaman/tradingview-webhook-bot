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
    broker_order_id: Optional[str] = None

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
                raw_sym = bp.get("symbol")
                asset_class = bp.get("asset_class", "us_equity")
                qty = abs(float(bp.get("qty", 0)))
                if qty == 0: continue
                
                # Alpaca represents crypto as BATUSD, we might have it as BATUSDT locally.
                possible_symbols = [raw_sym]
                if asset_class == "crypto" or (raw_sym.endswith("USD") and raw_sym != "USD"):
                    if raw_sym.endswith("USD"):
                        possible_symbols.append(raw_sym + "T")
                
                # Check if we already have it locally
                local_pos = next((p for p in self.positions.values() if p.symbol in possible_symbols and p.status == "OPEN"), None)
                
                # If we don't have it locally, add it
                if not local_pos:
                    # Choose standard symbol (prefer USDT for crypto to match TV)
                    sym = possible_symbols[-1] if (asset_class == "crypto" and len(possible_symbols) > 1) else raw_sym
                    market = "CRYPTO" if asset_class == "crypto" or raw_sym.endswith("USD") else "NASDAQ"

                    entry_price = float(bp.get("avg_entry_price", 0))
                    current_price = float(bp.get("current_price", entry_price))
                    side = "BUY" if float(bp.get("qty", 0)) > 0 else "SELL"
                    
                    # Estimate limits since broker might not return bracket details easily via /positions
                    tp_price = entry_price * 1.05 if side == "BUY" else entry_price * 0.95
                    sl_price = entry_price * 0.98 if side == "BUY" else entry_price * 1.02
                    
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
                        break_even_trigger_price=entry_price * 1.02 if side == "BUY" else entry_price * 0.98,
                        opened_at=datetime.now(timezone.utc).isoformat(),
                        unrealized_pnl=float(bp.get("unrealized_pl", 0)),
                        unrealized_pnl_pct=float(bp.get("unrealized_plpc", 0)) * 100
                    )
                    self.positions[pos.id] = pos
                else:
                    # LOCAL'DE VARSA: Alpaca'nın GERÇEK gerçekleşme (Fill) fiyatını ve miktarını senkronize et
                    # Bu sayede TradingView ile Alpaca arasındaki fiyat/makas (slippage) farkı kâr/zarar hesabını bozmaz!
                    real_entry_price = float(bp.get("avg_entry_price", 0))
                    if real_entry_price > 0:
                        local_pos.entry_price = real_entry_price
                        local_pos.quantity = qty
                        local_pos.nominal_value = real_entry_price * qty
            
            # Save the synced state to local db
            self.save_state()
        except Exception as e:
            from core.logger import logger
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
        except Exception as e:
            from core.logger import logger
            logger.error(f"State load error: {e}")

    def save_state(self):
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
                "positions": {pid: p.dict() for pid, p in self.positions.items()}
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
        # Temel tahsis yerine confidence_score ile dinamik Kelly ölçeklemesi
        # Confidence %50 ise %2 tahsis, %100 ise %8 tahsis
        alloc_pct = 0.02 + (confidence_score - 0.5) * 0.12 if confidence_score >= 0.5 else 0.02
        alloc_pct = max(0.01, min(0.08, alloc_pct)) # %1 ile %8 arası sınırlandır
        
        try:
            from services.engine.supervisor_agent import supervisor_agent
            multiplier = supervisor_agent.calculate_dynamic_budget_multiplier(self.market_prices)
        except ImportError:
            multiplier = 1.0
            
        base_capital = round(self.total_account_equity * alloc_pct, 2)
        adjusted_capital = base_capital * multiplier
        
        # En az 10$, en fazla bakiyenin %99'u kadar
        cap = max(10.0, min(adjusted_capital, self.total_account_equity * 0.99))
        
        # KULLANICI TALEBİ: Kesinlikle 500$ üzerinde alım yapılamaz (Hard Limit)
        cap = min(cap, 500.0)
        
        # Kesin Alpaca bütçe uyumluluğu: Serbest nakitin %95'ini geçemez
        return min(cap, max(10.0, self.available_cash * 0.95))

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
            
            price = data["price"]
            change_pct = data["change_pct"]
            high = data["high"]
            low = data["low"]
            market_type = data["market"]

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
                "source": "TRADINGVIEW_REALTIME_FEED",
                "last_update": datetime.now(TRT).strftime("%H:%M:%S")
            }

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

    def open_position(self, symbol: str, capital: Optional[float] = None, side: str = "BUY", tp_pct: float = 3.0, sl_pct: float = 1.5, entry_price_override: Optional[float] = None, atr_value: float = 0.0, use_chandelier_exit: bool = True, qty_override: Optional[float] = None, status: str = "OPEN") -> Optional[ActivePosition]:
        # MAKRO FORESIGHT KORUMASI: Serbest bakiyeyi güvende tut.
        if self.is_macro_standby:
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

        open_count = len([p for p in self.positions.values() if p.status == "OPEN"])
        if open_count >= 15 or self.available_cash < 10.0 or capital > self.available_cash:
            logger.warning(f"BÜTÇE LİMİTİ AŞILDI (Alpaca uyumlu): {sym} İşlemi reddedildi. İstenen: ${capital}, Serbest Nakit: ${self.available_cash}")
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

        if side == "BUY":
            tp_price = round(entry_price * (1.0 + (tp_pct / 100.0)), decimals)
            sl_price = round(entry_price * (1.0 - (sl_pct / 100.0)), decimals)
            be_trigger = round(entry_price * 1.025, decimals) # %2.50 kârda Break-Even
        else:
            tp_price = round(entry_price * (1.0 - (tp_pct / 100.0)), decimals)
            sl_price = round(entry_price * (1.0 + (sl_pct / 100.0)), decimals)
            be_trigger = round(entry_price * 0.975, decimals) # %2.50 kârda Break-Even

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
            status=status
        )

        # Broker emri başarılı olmadan pozisyonu lokal olarak OPEN kabul etme.
        if market in ["NASDAQ", "CRYPTO"]:
            try:
                from services.broker.factory import get_broker
                from core.config import settings
                is_paper = settings.trading_mode.upper() != "LIVE"
                broker = get_broker("ALPACA", paper=is_paper)
                if broker and broker.api:
                    if market == "CRYPTO":
                        # Kriptoda makas (spread) kaybını önlemek için 0.5% (binde 5) kayma toleransıyla limit order at
                        limit_prc = round(entry_price * 1.005, 4 if entry_price < 1.0 else 2) if side == "BUY" else round(entry_price * 0.995, 4 if entry_price < 1.0 else 2)
                        res = broker.place_market_order(
                            symbol=sym,
                            side=side,
                            qty=qty,
                            limit_price=limit_prc
                        )
                    else:
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
                        logger.info(f"[ALPACA BRACKET] {sym} emir başarıyla iletildi. OrderID: {res.get('order_id')}")
                    else:
                        logger.error(f"[ALPACA REJECTED] {sym}: {res.get('message', '?')}")
                        return None
                else:
                    logger.error(f"[ALPACA UNAVAILABLE] {sym}: broker API hazır değil.")
                    return None
            except Exception as e:
                logger.error(f"[ALPACA HATA] {sym} broker iletimi başarısız: {e}")
                return None

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
        Tam Otonom (Fully Autonomous) Al-Sat Motoru.
        Piyasa açıkken sürekli olarak fırsatları kollar ve yüksek güven skorlu hedeflere otomatik girer.
        """
        now = time.time()
        # Her 5 saniyede bir kontrol et ki piyasaya ve işlemciye aşırı yük binmesin
        if now - self.last_autonomous_check < 5.0:
            return
        self.last_autonomous_check = now
        
        active_positions = [p for p in self.positions.values() if p.status == "OPEN"]
        
        crypto_count = len([p for p in active_positions if p.market == "CRYPTO"])
        stock_count = len([p for p in active_positions if p.market in ["NASDAQ", "BIST", "STOCK"]])
        
        if crypto_count + stock_count >= 8:
            return  # Kasa riski yönetimi: Genel maksimum 8 aktif pozisyon (4 Kripto + 4 Hisse)
            
        try:
            from routers.market_router import matrix_results
            for m in matrix_results:
                sym = m.get("symbol", "")
                market = m.get("market", "")
                score = m.get("confidence_score", 0.0)
                vol_ratio = m.get("volume_ratio", 1.0)
                decision = m.get("decision", "WAIT")
                
                # Halihazırda bu varlıkta açık işlemimiz (veya Gölge İşlemimiz) varsa pas geç
                has_pos = any(p.symbol == sym and p.status == "OPEN" for p in self.positions.values())
                has_shadow = any(p.symbol == sym and "SHADOW_OPEN" in p.status for p in self.shadow_positions.values())
                if has_pos or has_shadow:
                    continue
                    
                # Piyasanın açık olup olmadığını teyit et
                from services.risk_engine.market_hours import market_hours_validator
                is_open, _, _ = market_hours_validator.is_market_open(sym)
                if not is_open:
                    continue
                    
                # BIST Koruması: BIST için otonom al-sat yapılmasın, sadece izlensin
                if market == "BIST":
                    continue
                    
                # Sepet (Portföy Çeşitlendirmesi) Koruması: Kriptoda max 4, Hisselerde max 4
                if market == "CRYPTO" and crypto_count >= 4:
                    continue
                if market != "CRYPTO" and stock_count >= 4:
                    continue
                    
                # TETİKLEME ŞARTI: Güven Skoru > 85, Hacim İvmesi > 1.2x ve Karar = BUY
                if score >= 85.0 and vol_ratio >= 1.2 and decision == "BUY":
                    # Kasa bütçesini tüketmemek için işlem başına 100$ - 300$ arası sabit bütçe
                    import random
                    auto_capital = random.uniform(100.0, 300.0)
                    # Pozisyon rollback: capital_allocated varsa iade et, yoksa nominal_value kullan
                    pos = None
                    refund = getattr(pos, 'capital_allocated', None) or getattr(pos, 'nominal_value', 0.0)
                    if self.available_cash < auto_capital:
                        auto_capital = self.available_cash # Eğer yeterli nakit yoksa eldekini kullan
                        
                    if auto_capital < 10.0:  # Minimum bütçe koruması
                        continue
                        
                    logger.info(f"🤖 [OTONOM MOTOR TETİKLENDİ] {sym} | Skor: {score} | Hacim: {vol_ratio}x. Sisteme otomatik alım emri gönderiliyor.")
                    
                    # İşlemi Sanal/Gerçek aç
                    self.open_position(
                        symbol=sym,
                        capital=auto_capital,
                        side="BUY",
                        tp_pct=3.0,
                        sl_pct=1.5
                    )
                    
                    # Tek bir döngüde maksimum 1 işlem açsın, spami engellesin.
                    break
        except Exception as e:
            logger.error(f"Otonom fırsat avcısı hatası: {e}")

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

            # STALENESS KORUMASI: last_updated_ts varsa ve 90 saniyeden eskiyse bekle.
            # last_updated_ts yoksa (statik fiyat) doğrudan devam et.
            if last_ts is not None and (time.time() - last_ts) > 90:
                logger.debug(f"[STALE PRICE] {pos.symbol} fiyat verisi eskidi ({int(time.time()-last_ts)}s) — değlendirme atlandı.")
                continue

            # API Hatalarına Karşı Güvenlik Kalkanı: Fiyat 0 veya negatifse işlem yapma!
            if curr_price <= 0.0:
                continue

            # Sadece simülasyon modunda yerel fiyatı arayüze yansıt (LIVE modda Alpaca senkronizasyonu devralır)
            if settings.trading_mode == "SIMULATION":
                pos.current_price = curr_price

            if pos.side == "BUY":
                # En yüksek fiyat güncellemesi (Trailing Stop İçin)
                if curr_price > pos.highest_price_seen:
                    pos.highest_price_seen = curr_price

                gross = (curr_price - pos.entry_price) * pos.quantity
                pct = ((curr_price - pos.entry_price) / pos.entry_price) * 100.0

                # === KAZAN-KAZAN: FLASH CRASH (HABER ETKİSİ) KORUMASI ===
                if pct <= -3.0 and not pos.trailing_stop_activated:
                    if is_open:
                        logger.warning(f"🚨 [FLASH CRASH DETECTED] {pos.symbol} %{pct:.2f} düştü! Acil stop tetikleniyor.")
                        self.close_position(pos_id, "CLOSED_FLASH_CRASH")
                        continue

                # AKILLI ÇIKIŞ (Erken Kâr Alma)
                # Eğer pozisyon %1.5'tan fazla kârdaysa ve momentum zayıflıyorsa (RSI aşırı şişmiş vs. veya hacim düştüyse)
                # Otonom Tarayıcı RSI verisine doğrudan erişemediğimizden fiyatın tepeden %1 düşüşüne de bakabiliriz.
                
                # İZLEYEN STOP (Dinamik Step-Up Trailing Stop)
                # Kâr arttıkça trailing mesafesi daralır.
                is_sniper = settings.current_risk_mode.upper() == "SNIPER"
                
                # Orijinal SL yüzdesini hesapla (eğer çok dar bir SL girilmişse, trailing de o kadar dar olmalı)
                orig_sl_pct = (pos.entry_price - pos.stop_loss_price) / pos.entry_price if pos.stop_loss_price < pos.entry_price else 0.03
                base_dist = 1.0 - min(orig_sl_pct, 0.02 if is_sniper else 0.03)

                # Dinamik mesafe hesaplama (Win-Win stratejisi)
                if pct > 4.0:
                    trailing_dist = 0.995 # %0.5 makas!
                elif pct > 2.0:
                    trailing_dist = 0.992 # %0.8 makas!
                elif pct > 1.0:
                    trailing_dist = 0.988 # %1.2 makas!
                elif pct > 0.5:
                    trailing_dist = 0.985 # %1.5 makas
                else:
                    trailing_dist = base_dist
                
                # İşleme girildiği andan itibaren her yükselişte anında iz sürer
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

                # 2. TP Kontrolü (+%3.0)
                if curr_price >= pos.target_profit_price:
                    if is_open:
                        self.close_position(pos_id, "CLOSED_TP")
                        continue

                # 3. SL / Trailing Stop Kontrolü
                if curr_price <= pos.stop_loss_price:
                    # === KAZAN-KAZAN: İLK 5 DAKİKA ERKEN STOP (STOP-HUNT) KORUMASI ===
                    import datetime
                    from dateutil import parser
                    opened_at_dt = parser.parse(pos.opened_at)
                    time_alive_secs = (datetime.datetime.now(datetime.timezone.utc) - opened_at_dt).total_seconds()
                    
                    if not pos.trailing_stop_activated and time_alive_secs < 300: # 5dk dolmadı
                        # Fiyat %3'ten fazla düşmediyse stop olma (gürültü filtresi)
                        if pct > -3.0:
                            logger.info(f"🛡️ [EARLY STOP SHIELD] {pos.symbol} açılalı {int(time_alive_secs)}s oldu. Geçici stop-hunt iptal (Kayıp: %{pct:.2f}).")
                            continue
                    
                    if is_open:
                        reason = "CLOSED_TRAILING" if pos.trailing_stop_activated else "CLOSED_SL"
                        self.close_position(pos_id, reason)
                        continue
            else:
                # SHORT (Açığa Satış) için Trailing Stop
                if pos.highest_price_seen == 0.0 or curr_price < pos.highest_price_seen:
                    pos.highest_price_seen = curr_price

                gross = (pos.entry_price - curr_price) * pos.quantity
                pct = ((pos.entry_price - curr_price) / pos.entry_price) * 100.0

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
