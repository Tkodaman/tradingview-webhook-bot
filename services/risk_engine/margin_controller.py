"""
Matematiksel Net Getiri, Komisyon, Slippage, BSMV ve Başa Baş (Break-Even) Risk Motoru

Formül:
Net Getiri = Brüt Fiyat Değişimi - (Alış Komisyonu + Satış Komisyonu + Kayma/Slippage + Vergi/BSMV)
"""

from typing import Dict, Any, Optional
from pydantic import BaseModel, Field

class ExactCostBreakdown(BaseModel):
    gross_pnl: float = Field(..., description="Brüt Fiyat Değişimi Tutarı ($ / ₺)")
    buy_commission: float = Field(..., description="Alış Komisyonu Tutarı")
    sell_commission: float = Field(..., description="Satış Komisyonu Tutarı")
    slippage_cost: float = Field(..., description="Giriş + Çıkış Kayma Payı (Slippage) Tutarı")
    tax_bsmv_cost: float = Field(..., description="BSMV ve Borsa Payı Tutarı")
    total_friction_costs: float = Field(..., description="Toplam Sürtünme Maliyeti (Komisyon + Kayma + Vergi)")
    net_pnl: float = Field(..., description="Net Ele Geçen Kâr / Zarar Tutarı")
    net_roi_pct: float = Field(..., description="Yüzdesel Net Getiri (%)")

class MarginCalculationRequest(BaseModel):
    account_size: float = Field(10000.0, description="Toplam Hesap Bakiyesi")
    risk_per_trade_pct: float = Field(1.0, description="İşlem Başı Maksimum Hesap Riski (%)")
    entry_price: float = Field(..., description="İşleme Giriş Fiyatı")
    symbol: str = Field("QQQ", description="Varlık Sembolü")
    market: str = Field("NASDAQ", description="BIST, NASDAQ, US, CRYPTO")
    action: str = Field("BUY", description="İşlem Yönü (BUY / SELL)")
    target_profit_pct: Optional[float] = None  # örn: +3.00%
    stop_loss_pct: Optional[float] = None      # örn: -1.50% (R:R >= 2.0)
    slippage_rate_pct: float = Field(0.08, description="Tek Yön Kayma Payı (%0.05 - %0.10)")
    max_position_margin_pct: float = Field(35.0, description="Tek İşleme Ayrılabilecek Maksimum Marj (%)")
    vix_or_volatility: Optional[float] = Field(None, description="VIX Endeksi veya ATR Volatilitesi")
    win_rate_pct: Optional[float] = Field(None, description="Strateji Başarı Oranı (%)")
    strat_streak_multiplier: float = Field(1.0, description="Darwinian Sermaye Çarpanı (1.0 = Normal, 2.0 = Av Serisi Bütçe Artışı, 0.5 = Can Yanması / Savunma)")

class AsymmetricMarginPlan(BaseModel):
    symbol: str
    market: str
    action: str
    nominal_entry_price: float
    slippage_adjusted_entry_price: float
    target_profit_price: float
    stop_loss_price: float
    break_even_trigger_price: float
    break_even_guaranteed_stop_price: float
    target_profit_pct: float
    stop_loss_pct: float
    risk_reward_ratio: str
    exact_shares_quantity: float
    position_nominal_value: float
    max_dollar_loss_allowed: float
    currency: str
    cost_breakdown_at_target: ExactCostBreakdown
    cost_breakdown_at_stop: ExactCostBreakdown
    break_even_protection_notes: str
    split_entry_prices: Optional[Dict[str, float]] = None
    capital_evolution_note: str = ""

class MathematicalNetReturnEngine:
    """
    Tüm Komisyon, BSMV, Borsa Payı ve Kayma (Slippage) Maliyetlerini
    Hassas Şekilde Hesaplayan Kurumsal Risk ve Başa Baş (Break-Even) Motoru
    """
    MARKET_DEFAULTS = {
        "BIST": {
            "default_tp_pct": 3.00,       # +%3.00 Kâr Al
            "default_sl_pct": 1.50,       # -%1.50 Stop Loss (R:R = 2.0:1)
            "commission_rate_pct": 0.20,  # Aracı kurum onbinde 20 (%0.20)
            "bsmv_rate_on_comm": 0.05,    # Komisyon üzerinden %5 BSMV
            "exchange_fee_pct": 0.005,    # Borsa Payı (%0.005)
            "slippage_pct": 0.08,         # %0.08 Kayma payı
            "be_trigger_pct": 1.00,       # +%1.00 kârda başa başa çekilir
            "currency": "₺"
        },
        "NASDAQ": {
            "default_tp_pct": 3.50,       # +%3.50 Kâr Al
            "default_sl_pct": 1.75,       # -%1.75 Stop Loss (R:R = 2.0:1)
            "commission_rate_pct": 0.10,  # %0.10 veya hisse başı
            "fixed_fee_usd": 0.50,        # Sabit borsa takas ücreti
            "bsmv_rate_on_comm": 0.0,
            "exchange_fee_pct": 0.003,    # SEC fee
            "slippage_pct": 0.07,         # %0.07 Kayma payı
            "be_trigger_pct": 1.20,
            "currency": "$"
        },
        "US": {
            "default_tp_pct": 3.50,
            "default_sl_pct": 1.75,
            "commission_rate_pct": 0.10,
            "fixed_fee_usd": 0.50,
            "bsmv_rate_on_comm": 0.0,
            "exchange_fee_pct": 0.003,
            "slippage_pct": 0.07,
            "be_trigger_pct": 1.20,
            "currency": "$"
        },
        "CRYPTO": {
            "default_tp_pct": 4.00,
            "default_sl_pct": 2.00,
            "commission_rate_pct": 0.10,  # Spot %0.10
            "fixed_fee_usd": 0.0,
            "bsmv_rate_on_comm": 0.0,
            "exchange_fee_pct": 0.0,
            "slippage_pct": 0.09,
            "be_trigger_pct": 1.50,
            "currency": "$"
        }
    }

    def calculate_costs_and_net_pnl(
        self,
        qty: float,
        entry_price: float,
        exit_price: float,
        market_cfg: Dict[str, Any],
        slippage_rate: float,
        action: str = "BUY"
    ) -> ExactCostBreakdown:
        nominal_buy_val = qty * entry_price
        nominal_sell_val = qty * exit_price
        
        if action == "BUY":
            gross_pnl = round(nominal_sell_val - nominal_buy_val, 4)
        else:
            # SHORT position: Profit is when exit_price < entry_price
            gross_pnl = round(nominal_buy_val - nominal_sell_val, 4)

        # 1. Alış Komisyonu
        buy_comm = (nominal_buy_val * (market_cfg["commission_rate_pct"] / 100.0)) + market_cfg.get("fixed_fee_usd", 0.0)
        # 2. Satış Komisyonu
        sell_comm = (nominal_sell_val * (market_cfg["commission_rate_pct"] / 100.0)) + market_cfg.get("fixed_fee_usd", 0.0)

        # 3. Kayma Payı (Slippage) = Girişte yukarıdan alma + Çıkışta aşağıdan satma
        slippage_cost = (nominal_buy_val * (slippage_rate / 100.0)) + (nominal_sell_val * (slippage_rate / 100.0))

        # 4. Vergi / BSMV / Borsa Payı
        bsmv = (buy_comm + sell_comm) * market_cfg.get("bsmv_rate_on_comm", 0.0)
        exchange_fee = (nominal_buy_val + nominal_sell_val) * (market_cfg.get("exchange_fee_pct", 0.0) / 100.0)
        total_tax = bsmv + exchange_fee

        # Toplam Sürtünme Maliyeti
        total_friction = buy_comm + sell_comm + slippage_cost + total_tax

        # NET GETİRİ FORMÜLÜ:
        # Net Getiri = Brüt PnL - (Alış Komisyonu + Satış Komisyonu + Slippage + BSMV/Vergi)
        net_pnl = gross_pnl - total_friction
        net_roi = (net_pnl / nominal_buy_val) * 100.0 if nominal_buy_val > 0 else 0.0

        return ExactCostBreakdown(
            gross_pnl=round(gross_pnl, 2),
            buy_commission=round(buy_comm, 2),
            sell_commission=round(sell_comm, 2),
            slippage_cost=round(slippage_cost, 2),
            tax_bsmv_cost=round(total_tax, 2),
            total_friction_costs=round(total_friction, 2),
            net_pnl=round(net_pnl, 2),
            net_roi_pct=round(net_roi, 2)
        )

    def calculate_plan(self, req: MarginCalculationRequest) -> AsymmetricMarginPlan:
        m_key = req.market.upper() if req.market.upper() in self.MARKET_DEFAULTS else "NASDAQ"
        cfg = self.MARKET_DEFAULTS[m_key]

        tp_pct = req.target_profit_pct if req.target_profit_pct else cfg["default_tp_pct"]
        sl_pct = req.stop_loss_pct if req.stop_loss_pct else cfg["default_sl_pct"]
        slip_rate = req.slippage_rate_pct if req.slippage_rate_pct else cfg["slippage_pct"]
        
        # Dinamik Slippage Ayarlaması (VIX/Volatilite)
        if req.vix_or_volatility:
            vix = req.vix_or_volatility
            if vix > 25.0:
                slip_rate *= 2.0  # Aşırı Korku/Oynaklık
            elif vix > 18.0:
                slip_rate *= 1.5  # Yüksek Volatilite
            elif vix < 13.0:
                slip_rate *= 0.5  # Sakin Piyasa, Düşük Slippage
        
        be_trigger_pct = cfg["be_trigger_pct"]
        currency = cfg["currency"]

        account = req.account_size
        risk_pct = req.risk_per_trade_pct
        
        # Kelly Criterion (Position Sizing)
        if req.win_rate_pct and req.win_rate_pct > 0:
            w = req.win_rate_pct / 100.0
            r = tp_pct / sl_pct
            kelly_pct = w - ((1.0 - w) / r)
            half_kelly_pct = (kelly_pct / 2.0) * 100.0
            if half_kelly_pct > 0:
                # Cüretkar ama güvenli Half-Kelly, maks %5 riskle sınırlandırılır
                risk_pct = min(half_kelly_pct, 5.0)
            else:
                # Dezavantajlı setup, minimum koruma riski
                risk_pct = 0.5

        # --- EKLENTİ 2: DARWINIAN KAPİTAL EVRİMİ (Sermaye Evrimi) ---
        # Stratejinin anlık başarı/kazanç ivmesine göre Kelly riskini katlıyoruz veya kısıyoruz.
        risk_pct = risk_pct * req.strat_streak_multiplier
        risk_pct = min(risk_pct, 20.0) # Bütçe %20'yi (Tavan) geçemez. Maksimum cephane.
        risk_pct = max(risk_pct, 0.5)  # %0.5'in altına (Taban) inemez. Minimum savunma.
        
        cap_note = "Standart Dağılım"
        if req.strat_streak_multiplier > 1.2:
            cap_note = "🧬 EVRİM: Av serisi tespit edildi! Kasadan stratejiye ayrılan cephane boyutu arttırıldı."
        elif req.strat_streak_multiplier < 0.8:
            cap_note = "🛡️ SAVUNMA: Strateji ardışık hasar aldı. Kasa koruma (Defans) moduna geçildi, bütçe kısıldı."

        entry = req.entry_price
        action = req.action.upper()
        max_margin_pct = req.max_position_margin_pct

        # Slippage etkili gerçek giriş fiyatı
        slip_entry = entry * (1.0 + (slip_rate / 100.0)) if action == "BUY" else entry * (1.0 - (slip_rate / 100.0))

        # Hedef TP ve Stop Seviyeleri
        if action == "BUY":
            tp_price = round(entry * (1.0 + (tp_pct / 100.0)), 4)
            sl_price = round(entry * (1.0 - (sl_pct / 100.0)), 4)
            be_trigger_price = round(entry * (1.0 + (be_trigger_pct / 100.0)), 4)
            
            # Başa baş (Break-Even) Stop Fiyatı = Giriş Fiyatı * (1 + Tüm Komisyon/Slippage/Vergi Oranı)
            # Fiyat buraya döndüğünde net pnl = 0.00 TL / $ olur
            friction_pct_total = (cfg["commission_rate_pct"] * 2) + (slip_rate * 2) + (cfg["commission_rate_pct"] * 2 * cfg["bsmv_rate_on_comm"]) + (cfg["exchange_fee_pct"] * 2)
            guaranteed_be_stop = round(entry * (1.0 + (friction_pct_total / 100.0)), 4)
            stop_distance = entry - sl_price
        else:
            tp_price = round(entry * (1.0 - (tp_pct / 100.0)), 4)
            sl_price = round(entry * (1.0 + (sl_pct / 100.0)), 4)
            be_trigger_price = round(entry * (1.0 - (be_trigger_pct / 100.0)), 4)
            friction_pct_total = (cfg["commission_rate_pct"] * 2) + (slip_rate * 2) + (cfg["commission_rate_pct"] * 2 * cfg["bsmv_rate_on_comm"]) + (cfg["exchange_fee_pct"] * 2)
            guaranteed_be_stop = round(entry * (1.0 - (friction_pct_total / 100.0)), 4)
            stop_distance = sl_price - entry

        # Sermaye ve Pozisyon Boyutlandırma
        max_allowed_risk_dollar = account * (risk_pct / 100.0)
        ideal_pos_val = max_allowed_risk_dollar / (sl_pct / 100.0)
        max_margin_cap = account * (max_margin_pct / 100.0)
        final_pos_val = min(ideal_pos_val, max_margin_cap)

        exact_qty = round(final_pos_val / entry, 4)
        rr_ratio = round(tp_pct / sl_pct, 2)

        # Kâr Hedefinde ve Stop Noktasında Tam Maliyet Ayrıştırması
        costs_at_tp = self.calculate_costs_and_net_pnl(exact_qty, entry, tp_price, cfg, slip_rate, action)
        costs_at_sl = self.calculate_costs_and_net_pnl(exact_qty, entry, sl_price, cfg, slip_rate, action)

        # Gerçek risk, stop noktasındaki net zarar (komisyon ve kayma dahil) mutlak değeridir.
        actual_risk_at_sl = round(abs(costs_at_sl.net_pnl), 2)

        notes = (
            f"[{m_key}] R:R Oranı {rr_ratio}:1. Fiyat +%{be_trigger_pct:.2f} kâra ({currency}{be_trigger_price:.2f}) ulaştığında "
            f"Stop-Loss otomatik olarak {currency}{guaranteed_be_stop:.2f} seviyesine çekilir. Bu seviyede komisyon, slippage ve BSMV "
            f"tamamen karşılanarak işlem sıfır riskli (Free-Roll) hale getirilir."
        )

        # --- EKLENTİ 1: MİKRO PUSU EMRİ (Geri Çekilme - Pullback Algoritması) ---
        split_entries = None
        if action == "BUY":
            pullback_price = round(entry * 0.985, 4) # Hacimli roketin %1.5 aşağısına "Pusu" kur.
            split_entries = {
                "market_buy_40_pct": entry,
                "limit_pusu_60_pct": pullback_price,
                "avg_blended_entry": round((entry * 0.40) + (pullback_price * 0.60), 4)
            }

        return AsymmetricMarginPlan(
            symbol=req.symbol,
            market=m_key,
            action=action,
            nominal_entry_price=entry,
            slippage_adjusted_entry_price=round(slip_entry, 4),
            target_profit_price=tp_price,
            stop_loss_price=sl_price,
            break_even_trigger_price=be_trigger_price,
            break_even_guaranteed_stop_price=guaranteed_be_stop,
            target_profit_pct=tp_pct,
            stop_loss_pct=sl_pct,
            risk_reward_ratio=f"{rr_ratio} : 1",
            exact_shares_quantity=exact_qty,
            position_nominal_value=round(final_pos_val, 2),
            max_dollar_loss_allowed=actual_risk_at_sl,
            currency=currency,
            cost_breakdown_at_target=costs_at_tp,
            cost_breakdown_at_stop=costs_at_sl,
            break_even_protection_notes=notes,
            split_entry_prices=split_entries,
            capital_evolution_note=cap_note
        )

margin_controller = MathematicalNetReturnEngine()
