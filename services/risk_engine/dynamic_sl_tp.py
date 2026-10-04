import asyncio
from core.logger import logger
from core.config import settings


def calculate_atr_based_tp_sl(
    entry_price: float,
    atr_value: float = 0.0,
    atr_pct: float = None,
    side: str = "BUY",
    is_crypto: bool = False,
    risk_mode: str = "AGGRESSIVE",
    regime: str = "SIDEWAYS",
) -> tuple:
    """
    Dinamik ATR ve Volatilite Bazlı Kâr Al (TP) ve Zarar Kes (SL) Hesaplayıcı.
    Kullanıcı Direktifi:
      - Sabit dar aralıklar (%2) piyasa gürültüsünde tehlikelidir, dinamik olmalı.
      - Hisse kafasını kaldırdığında kârı cebe indirmeli (hızlı TP).
      - Kırmızıya dönünce aşık olmadan küçük bir zararla kapatmalı (sağlam SL).
      - Varlığın gerçek oynaklığına (ATR) ve piyasa rejimine göre dinamik nefes payı bırakılmalı.
    """
    if entry_price <= 0:
        return (3.0 if not is_crypto else 4.5), (1.8 if not is_crypto else 2.5)

    # 1. Efektif ATR Yüzdesini Belirle
    if atr_pct is not None and atr_pct > 0:
        eff_atr_pct = float(atr_pct)
    elif atr_value > 0 and entry_price > 0:
        eff_atr_pct = (atr_value / entry_price) * 100.0
    else:
        # Fallback volatilite varsayımı
        eff_atr_pct = 3.2 if is_crypto else 1.6

    mode = (risk_mode or "AGGRESSIVE").upper()
    is_short_term = mode in ["SNIPER", "AGGRESSIVE"]

    # 2. Dinamik Stop-Loss (SL) Hesabı
    # Varlığın normal mum oynaklığının (ATR) dışına konulur, böylece "stop-hunt" ve fitil gürültüsünden kaçınılır.
    if is_crypto:
        # Kripto: fitiller daha sert, ATR çarpanı 1.4x - 1.6x
        sl_mult = 1.35 if is_short_term else 1.55
        calculated_sl = eff_atr_pct * sl_mult
        # Kripto sınırları: Asgari %2.0, Azami %4.8 (gün içi sermaye korunur)
        min_sl = 2.0
        max_sl = 4.8 if is_short_term else 6.0
    else:
        # Hisse Senetleri (NASDAQ / BIST): ATR çarpanı 1.25x - 1.45x
        sl_mult = 1.25 if is_short_term else 1.45
        calculated_sl = eff_atr_pct * sl_mult
        # Hisse sınırları: Asgari %1.4, Azami %3.2 (hızlı kesme)
        min_sl = 1.4
        max_sl = 3.2 if is_short_term else 4.5

    sl_pct = max(min_sl, min(calculated_sl, max_sl))

    # 3. Dinamik Kâr Al (TP) Hesabı
    # Hantal %10 rallileri beklemez; volatiliteye göre hızlıca kârı cebe indirir.
    # Risk-Ödül Oranı (R:R) en az 1.35x - 1.50x korunur.
    import json, os
    dyn_tp_modifier = 1.0
    dyn_sl_modifier = 1.0
    try:
        if os.path.exists("data/dynamic_thresholds.json"):
            with open("data/dynamic_thresholds.json", "r") as f:
                dyn = json.load(f)
                dyn_tp_modifier = dyn.get("tp_multiplier_adjustment", 1.0)
                dyn_sl_modifier = dyn.get("sl_multiplier_adjustment", 1.0)
    except: pass

    if is_crypto:
        calculated_tp = 3.5 * dyn_tp_modifier  # Otonom Makine Öğrenimi Çarpanı
        min_tp = 3.5 * dyn_tp_modifier
        max_tp = 3.5 * dyn_tp_modifier
    else:
        tp_mult = (1.25 if is_short_term else 1.60) * dyn_tp_modifier
        calculated_tp = eff_atr_pct * tp_mult
        min_rr = 1.15 if is_short_term else 1.25
        min_tp = max(1.5, sl_pct * min_rr)
        max_tp = 3.5 if is_short_term else 6.0
        
    sl_pct = sl_pct * dyn_sl_modifier

    tp_pct = max(min_tp, min(calculated_tp, max_tp))

    # 4. Rejim Düzeltmeleri
    if regime in ["BEAR", "CRASH"]:
        # Ayı veya Çöküş rejiminde kâr alma daha da hızlı olmalı (reversal yemeden çık)
        tp_pct = max(min_tp * 0.9, tp_pct * 0.85)
    elif regime == "MEGA_BULL":
        # Güçlü boğada kâr hedefi hafifçe esneyebilir
        tp_pct = min(max_tp, tp_pct * 1.15)

    from core.logger import logger
    logger.info(
        f"🎯 [DYNAMIC ATR TP/SL] entry={entry_price:.2f} ATR%={eff_atr_pct:.2f}% "
        f"({mode}/{regime}/{'CRYPTO' if is_crypto else 'STOCK'}) -> "
        f"TP=%{tp_pct:.2f} | SL=%{sl_pct:.2f} | R:R={tp_pct/sl_pct:.2f}"
    )
    return round(tp_pct, 2), round(sl_pct, 2)
class DynamicRiskManager:
    def __init__(self):
        # symbol -> { "high_water_mark": float, "initial_sl_set": bool }
        self.price_history = {}

        # === ÖZGÜVENLİ TRAILING STOP PARAMETRESİ ===
        # trailing_distance_pct: Kârın izini sürerken sahte iğnelere (wicks) kurban gitmemek için ESNETİLDİ.
        # Çok sıkı (%2) trailing stop, ufak bir düzeltmede (pullback) kârlı işlemi zararına kapatıyordu.
        self.trailing_distance_pct = 4.8   # %4.8 dinamik iz sürme (Geniş Nefes Payı Bırakıldı - Wick Guard)

    async def on_price_update(self, symbol: str, current_price: float):
        """
        Her tick'te cagrilir. SL = max(mevcut_SL, current_price * (1 - 0.015))
        Asla asagi inmez. Aktivasyon esigi yok — giri anından itibaren aktif.
        """
        if symbol not in self.price_history:
            self.price_history[symbol] = {
                "high_water_mark": current_price,
                "initial_sl_set": False
            }

        history = self.price_history[symbol]

        # Zirveyi güncelle (asla aşağı gitme)
        if current_price > history["high_water_mark"]:
            history["high_water_mark"] = current_price

        await self._evaluate_trailing_stop(symbol, current_price, history)

    async def _evaluate_trailing_stop(self, symbol: str, current_price: float, history: dict):
        from services.market_feed.live_stream import live_trade_manager

        matched_pos = None
        for pos_id, pos in live_trade_manager.positions.items():
            if pos.symbol == symbol and pos.status == "OPEN":
                matched_pos = pos
                break

        if not matched_pos:
            return

        entry_price  = matched_pos.entry_price
        current_sl   = matched_pos.stop_loss_price
        
        # Otonom Makas (Dinamik Evrim - Stop-Hunt Kaçınma)
        try:
            from services.risk_engine.stop_hunt_evader import stop_hunt_evader
            profile = stop_hunt_evader.analyze_asset(symbol)
            trail_pct = (self.trailing_distance_pct * profile["sl_multiplier"]) / 100.0
        except Exception:
            trail_pct = self.trailing_distance_pct / 100.0

        if matched_pos.side == "BUY":
            # === Chandelier Exit (ATR bazlı) ===
            if getattr(matched_pos, "use_chandelier_exit", False) and getattr(matched_pos, "atr_value", 0.0) > 0:
                try:
                    from services.engine.risk_engine import RiskEngine
                    new_sl = RiskEngine.calculate_atr_trailing_stop(
                        current_price=history["high_water_mark"],
                        atr=matched_pos.atr_value,
                        direction="LONG",
                        asset_type="CRYPTO" if matched_pos.market == "CRYPTO" else "STOCK",
                        ticker=symbol
                    )
                except Exception as e:
                    new_sl = history["high_water_mark"] - (matched_pos.atr_value * 3.0)

                if new_sl > current_sl:
                    logger.info(f"[CHANDELIER ML-WICK] {symbol} SL {current_sl:.4f} -> {new_sl:.4f} (Dinamik Zırh)")
                    matched_pos.stop_loss_price = round(new_sl, 4)
                    await self._update_broker_sl(symbol, matched_pos.target_profit_price, matched_pos.stop_loss_price, matched_pos.market)
                    await self._notify_ui(symbol, matched_pos)
                return

            # === %1.5 SIKI TRAILING STOP ===
            # SL = en yüksek görülen fiyatın %1.5 altı
            # İlk SL: giriş fiyatının %1.5 altı (eğer mevcut SL daha uzaksa ezip geçer)
            candidate_sl = history["high_water_mark"] * (1.0 - trail_pct)

            # SL'yi asla aşağı indirme; her zaman en yüksek olanı kullan
            new_sl_rounded = round(max(candidate_sl, current_sl), 4)
            current_sl_rounded = round(current_sl, 4)

            # Değişim varsa güncelle
            if new_sl_rounded > current_sl_rounded:
                profit_pct = ((current_price - entry_price) / entry_price) * 100.0
                logger.info(
                    f"[TRAILING SL] {symbol} | Fiyat={current_price:.4f} "
                    f"| HWM={history['high_water_mark']:.4f} "
                    f"| SL {current_sl_rounded:.4f} -> {new_sl_rounded:.4f} "
                    f"| PnL={profit_pct:+.2f}%"
                )
                matched_pos.stop_loss_price = new_sl_rounded
                await self._update_broker_sl(symbol, matched_pos.target_profit_price, matched_pos.stop_loss_price, matched_pos.market)
                await self._notify_ui(symbol, matched_pos)

        elif matched_pos.side == "SELL":
            # === Chandelier Exit (ATR bazlı) ===
            if getattr(matched_pos, "use_chandelier_exit", False) and getattr(matched_pos, "atr_value", 0.0) > 0:
                try:
                    from services.engine.risk_engine import RiskEngine
                    low_mark = history.get("low_water_mark", current_price)
                    new_sl = RiskEngine.calculate_atr_trailing_stop(
                        current_price=low_mark,
                        atr=matched_pos.atr_value,
                        direction="SHORT",
                        asset_type="CRYPTO" if matched_pos.market == "CRYPTO" else "STOCK",
                        ticker=symbol
                    )
                except Exception as e:
                    new_sl = history.get("low_water_mark", current_price) + (matched_pos.atr_value * 3.0)

                if new_sl < current_sl:
                    logger.info(f"[CHANDELIER ML-WICK] {symbol} SELL SL {current_sl:.4f} -> {new_sl:.4f} (Dinamik Zırh)")
                    matched_pos.stop_loss_price = round(new_sl, 4)
                    await self._update_broker_sl(symbol, matched_pos.target_profit_price, matched_pos.stop_loss_price, matched_pos.market)
                    await self._notify_ui(symbol, matched_pos)
                return

            # SELL trailing: SL = en düşük fiyatın %1.5 üstü
            low_water = min(current_price, history.get("low_water_mark", current_price))
            if current_price < history.get("low_water_mark", current_price):
                history["low_water_mark"] = current_price
            candidate_sl = history.get("low_water_mark", current_price) * (1.0 + trail_pct)
            
            new_sl_rounded = round(min(candidate_sl, current_sl), 4)
            current_sl_rounded = round(current_sl, 4)
            
            if new_sl_rounded < current_sl_rounded:
                logger.info(f"[TRAILING SL] {symbol} SELL SL {current_sl_rounded:.4f} -> {new_sl_rounded:.4f}")
                matched_pos.stop_loss_price = new_sl_rounded
                await self._update_broker_sl(symbol, matched_pos.target_profit_price, matched_pos.stop_loss_price, matched_pos.market)
                await self._notify_ui(symbol, matched_pos)

    async def _update_broker_sl(self, symbol: str, tp_price: float, sl_price: float, market: str):
        if settings.trading_mode in ["LIVE", "PAPER"]:
            from services.broker.factory import get_broker
            broker = get_broker(market)
            if broker and hasattr(broker, 'update_bracket_orders'):
                res = broker.update_bracket_orders(symbol, take_profit_price=tp_price, stop_loss_price=sl_price)
                if res.get("status") == "success":
                    logger.info(f"✅ [BROKER SYNC] {symbol} yeni makas (TP/SL) borsaya ({market}) islendi.")
                else:
                    logger.warning(f"⚠️ [BROKER SYNC ERROR] {symbol} borsaya islenemedi: {res}")

    async def _notify_ui(self, symbol: str, position):
        from routers.websocket_router import manager
        await manager.broadcast({
            "type": "DYNAMIC_SPREAD_UPDATE",
            "symbol": symbol,
            "new_sl": position.stop_loss_price,
            "new_tp": position.target_profit_price,
            "message": f"🤖 YZ Makas Guncellemesi: {symbol} yeni Stop-Loss: ${position.stop_loss_price:.4f}"
        })

dynamic_risk_manager = DynamicRiskManager()
