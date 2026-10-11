import asyncio
import time
from core.logger import logger
from core.config import settings


class WickShield:
    """
    3 Dakikalık Mum Kapanış / Fitil Koruması (Wick-Shield).
    Piyasa yapıcıların ve balinaların attığı anlık silkeleme iğnelerine (stop-hunt / fake wick)
    karşı korur. Fiyat stop-loss çizgisini ihlal ettiğinde hemen piyasa emriyle
    pozisyonu kapatmaz; 3 dakika (180 saniye) boyunca teyit bekler.
    
    - Eğer fiyat 3 dakika içinde tekrar SL seviyesinin üstüne toparlarsa (fitil/silkeleme):
      Sayaç sıfırlanır, tuzak başarıyla atlatılmış sayılır.
    - Eğer Nükleer Çöküş (Hard Crash) varsa (SL'nin %3.0 daha altına sert sarkarsa):
      Süre beklenmeden sermayeyi kurtarmak için acil çıkış tetiklenir.
    - Eğer 3 dakika boyunca SL altında kalmaya devam ederse:
      Mum gövdesiyle kırılım teyit edilmiş sayılır ve stop tetiklenir.
    """
    def __init__(self, confirmation_window_sec: int = 180):
        self.confirmation_window_sec = confirmation_window_sec  # 3 dk (180 sn)
        self.breach_timestamps = {}  # pos_id -> timestamp

    def evaluate_sl_breach(self, pos_id: str, symbol: str, current_price: float, sl_price: float, is_crypto: bool = True) -> tuple:
        """
        Döner: (should_exit: bool, reason: str, remaining_sec: float)
        """
        now = time.time()
        if sl_price <= 0:
            return False, "Geçersiz SL", 0.0

        # Hard Crash Koruması: Fiyat SL'nin %3.0 altına indiyse fitil değil gerçek çöküştür
        crash_dist = 0.970 if is_crypto else 0.985
        hard_sl_price = sl_price * crash_dist
        if current_price < hard_sl_price:
            self.breach_timestamps.pop(pos_id, None)
            return True, "NÜKLEER ÇÖKÜŞ (Hard Crash - SL %3.0 aşıldı)", 0.0

        # İlk ihlal anı
        if pos_id not in self.breach_timestamps:
            self.breach_timestamps[pos_id] = now
            logger.info(f"🛡️ [WICK-SHIELD AKTİF] {symbol} SL ({sl_price:.4f}) altına sarktı (Fiyat: {current_price:.4f}). 3 Dakikalık Fitil Koruması başladı!")
            return False, "İğne Filtresi devrede (Teyit bekleniyor)", self.confirmation_window_sec

        elapsed = now - self.breach_timestamps[pos_id]
        remaining = max(0.0, self.confirmation_window_sec - elapsed)

        if elapsed >= self.confirmation_window_sec:
            self.breach_timestamps.pop(pos_id, None)
            return True, f"3 Dakika Mum Kapanış Teyidi Alındı ({int(elapsed)}s)", 0.0

        return False, f"İğne Koruması ({int(remaining)}s kaldı)", remaining

    def reset_breach(self, pos_id: str, symbol: str = ""):
        if pos_id in self.breach_timestamps:
            self.breach_timestamps.pop(pos_id, None)
            logger.info(f"💎 [WICK-SHIELD BAŞARILI] {symbol} SL seviyesinin üstüne toparladı! Balina silkelemesi başarıyla atlatıldı.")


wick_shield = WickShield(confirmation_window_sec=180)


def calculate_atr_based_tp_sl(
    entry_price: float,
    atr_value: float = 0.0,
    atr_pct: float = None,
    side: str = "BUY",
    is_crypto: bool = False,
    risk_mode: str = "AGGRESSIVE",
    regime: str = "SIDEWAYS",
    symbol: str = "UNKNOWN",
    volume_spike: float = 1.0,
    is_breakout: bool = False,
    depth_ratio: float = 1.0,
    spread_pct: float = 0.05
) -> tuple:
    """
    Dinamik ATR, Tahta Derinliği, Rejim ve DARWIN EVRİM ÖĞRENİMİ Bazlı Kâr Al (TP) ve Zarar Kes (SL) Hesaplayıcı.
    Kullanıcı Direktifleri:
      - Sabit dar stop barajı (%1.5 - %2.5) imha edildi! Asgari SL: ATR x 1.8 (Minimum %3.5 - %4.5).
      - Kırılım ve füze yakalandığında kâr hedefleri (TP) dar %3'ten dinamik %4 - %7 bandına açılır.
      - Her varlık için tahta derinliği (Order Book Depth) ve grafiğin doğal ATR nefes payına göre esnek makas belirlenir.
      - Anlık iğnelerde stop olmamak için 3 Dakikalık Mum Kapanış Filtresi (Wick-Shield) korunur.
    """
    if entry_price <= 0:
        return (5.0 if is_crypto else 3.0), (4.0 if is_crypto else 1.8)

    # 1. Efektif ATR Yüzdesini Belirle
    if atr_pct is not None and atr_pct > 0:
        eff_atr_pct = float(atr_pct)
    elif atr_value > 0 and entry_price > 0:
        eff_atr_pct = (atr_value / entry_price) * 100.0
    else:
        # Fallback volatilite varsayımı
        eff_atr_pct = 2.8 if is_crypto else 1.6

    mode = (risk_mode or "AGGRESSIVE").upper()
    is_short_term = mode in ["SNIPER", "AGGRESSIVE"]

    # ========================================================
    # 2. DİNAMİK STOP-LOSS (SL) - ATR x 1.8 & TAHTA DERİNLİĞİ
    # ========================================================
    if is_crypto:
        # Kriptoda flama/iğne ve doğal solunum payı: ATR x 1.80
        sl_mult = 1.80 if is_short_term else 2.05
        calculated_sl = eff_atr_pct * sl_mult

        # Tahta Derinliği (Order Book) Uyarlaması:
        # Eğer tahtada satıcı baskısı yüksekse (depth_ratio < 0.8), balina fitili payı için SL %0.3 esnetilir
        depth_sl_buffer = 0.35 if (depth_ratio and depth_ratio < 0.8) else 0.0

        # Asgari SL Tabanı: Normal kriptoda asgari %3.5, volatilite yüksekse (ATR >= %2.5) asgari %4.5
        min_sl = (4.5 if eff_atr_pct >= 2.5 else 3.5) + depth_sl_buffer
        max_sl = 6.8 if is_short_term else 7.8  # Sermaye koruma üst tavanı
        sl_pct = max(min_sl, min(calculated_sl + depth_sl_buffer, max_sl))
    else:
        # Hisse Senetleri (NASDAQ / BIST): ATR çarpanı 1.25x - 1.45x
        sl_mult = 1.25 if is_short_term else 1.45
        calculated_sl = eff_atr_pct * sl_mult
        min_sl = 1.4
        max_sl = 3.2 if is_short_term else 4.5
        sl_pct = max(min_sl, min(calculated_sl, max_sl))

    # ========================================================
    # 🧬 3. DARWIN EVRİM ÖĞRENİMİ (WICK-EVADER) MODÜLÜ
    # ========================================================
    import json, os
    dyn_tp_modifier = 1.0
    dyn_sl_modifier = 1.0
    darwin_wick_multiplier = 1.0

    try:
        if os.path.exists("data/dynamic_thresholds.json"):
            with open("data/dynamic_thresholds.json", "r") as f:
                dyn = json.load(f)
                dyn_tp_modifier = dyn.get("tp_multiplier_adjustment", 1.0)
                dyn_sl_modifier = dyn.get("sl_multiplier_adjustment", 1.0)
    except Exception:
        pass

    try:
        if os.path.exists("data/darwin_genetics.json") and symbol != "UNKNOWN":
            with open("data/darwin_genetics.json", "r") as f:
                genetics = json.load(f)
                if symbol in genetics:
                    darwin_wick_multiplier = genetics[symbol].get("wick_multiplier", 1.0)
    except Exception:
        pass

    sl_pct = sl_pct * dyn_sl_modifier * darwin_wick_multiplier

    # ========================================================
    # 🚀 4. DİNAMİK KÂR HEDEFİ (TP) - DİNAMİK %4.0 - %7.0 BANDI
    # ========================================================
    if is_crypto:
        # [KULLANICI DİREKTİFİ - DİNAMİK %4 - %7 BANDI]
        is_explosive = is_breakout or (volume_spike and volume_spike >= 2.0)

        # Kırılım / Füze modunda hedefler %5.5 - %7.0, standart dalgalanmada %4.0 - %5.5
        min_tp = 4.0 * dyn_tp_modifier
        max_tp = 7.0 * dyn_tp_modifier

        if is_explosive:
            tp_mult = 2.1 if is_short_term else 2.4
            calculated_tp = max(5.2, eff_atr_pct * tp_mult) * dyn_tp_modifier
        else:
            tp_mult = 1.6 if is_short_term else 1.9
            calculated_tp = max(4.0, eff_atr_pct * tp_mult) * dyn_tp_modifier

        # R:R Güvencesi: Kâr hedefi en az SL * 1.15 olmalı (üst sınır %7.0 aşılmaz)
        min_tp = max(min_tp, min(sl_pct * 1.15, max_tp))
        tp_pct = max(min_tp, min(calculated_tp, max_tp))
    else:
        tp_mult = (1.25 if is_short_term else 1.60) * dyn_tp_modifier
        calculated_tp = eff_atr_pct * tp_mult
        min_rr = 1.15 if is_short_term else 1.25
        min_tp = max(1.5, sl_pct * min_rr)
        max_tp = 3.5 if is_short_term else 6.0
        tp_pct = max(min_tp, min(calculated_tp, max_tp))

    # 5. Rejim Düzeltmeleri
    if regime in ["BEAR", "CRASH"]:
        tp_pct = max(min_tp * 0.9, tp_pct * 0.85)
    elif regime == "MEGA_BULL":
        tp_pct = min(max_tp, tp_pct * 1.10)

    logger.info(
        f"🎯 [DYNAMIC ATR TP/SL] entry={entry_price:.4f} ATR%={eff_atr_pct:.2f}% "
        f"({mode}/{regime}/{'CRYPTO' if is_crypto else 'STOCK'}) -> "
        f"TP=%{tp_pct:.2f} | SL=%{sl_pct:.2f} | R:R={tp_pct/sl_pct:.2f}"
    )
    return round(tp_pct, 2), round(sl_pct, 2)

class DynamicRiskManager:
    def __init__(self):
        # symbol -> { "high_water_mark": float, "initial_sl_set": bool }
        self.price_history = {}

        # === ÖZGÜVENLİ TRAILING STOP PARAMETRESİ ===
        # Kullanıcı Direktifi: Kâra geçtikten sonra kazancı korumak (kazı) için maksimum %2 dinamik iz sürme.
        self.trailing_distance_pct = 2.0   # Kâra geçildiğinde zirveden %2 geri çekilme hakkı tanınır.

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
        
        # Dinamik İz Sürme Mesafesi (Kullanıcı Direktifi: Volatiliteye Göre %1.5 ile %2.5 arası)
        try:
            from services.risk_engine.stop_hunt_evader import stop_hunt_evader
            profile = stop_hunt_evader.analyze_asset(symbol)
            base_trail = (self.trailing_distance_pct * profile["sl_multiplier"]) / 100.0
        except Exception:
            base_trail = self.trailing_distance_pct / 100.0
            
        # Volatilite (ATR) veya Kripto durumuna göre Dinamik İz Süren (Trailing) Mesafesi
        is_crypto = matched_pos.market == "CRYPTO"
        eff_atr_pct = (getattr(matched_pos, "atr_value", 0.0) / entry_price * 100.0) if entry_price > 0 else 0.0
        
        if is_crypto or eff_atr_pct > 2.0:
            trail_pct = max(base_trail, 0.025) # Volatil varlıksa %2.5
        else:
            trail_pct = max(base_trail, 0.015) # Ağır varlıksa minimum %1.5

        # --- KULLANICI DİREKTİFİ: PARABOLİK İZ SÜRME VE HACİM SENSÖRÜ ---
        profit_pct_hwm = ((history.get("high_water_mark", current_price) - entry_price) / entry_price) * 100.0 if matched_pos.side == "BUY" else ((entry_price - history.get("low_water_mark", current_price)) / entry_price) * 100.0
        
        if profit_pct_hwm > 6.0:
            trail_pct = 0.008 # %6 kârın üstünde makası acımasızca daralt (%0.8)
        elif profit_pct_hwm > 3.0:
            trail_pct = 0.012 # %3 kârın üstünde dar takip (%1.2)
            
        from datetime import datetime, timezone
        try:
            opened_time = datetime.fromisoformat(matched_pos.opened_at.replace("Z", "+00:00"))
            hours_open = (datetime.now(timezone.utc) - opened_time).total_seconds() / 3600.0
        except Exception:
            hours_open = 0.0
            
        # PUMP / DUMP Algılayıcı (Hızlı Kâr Şiddeti)
        if hours_open < 1.0 and profit_pct_hwm >= 4.0:
            trail_pct = 0.005 # Aşırı hızlı PUMP! Kalkanı anında %0.5'e düşür, tepeden çakılmadan kaç.

        # --- KULLANICI DİREKTİFİ: TIME-DECAY (8 SAAT) ---
        # İşlem yatayda 8 saat kalırsa, başlangıç kalkanı (sl_pct) yavaş yavaş entry_price'a doğru çekilerek boğulur.
        decay_ratio = min(hours_open / 8.0, 1.0) if hours_open > 0 else 0.0


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

                if round(new_sl, 4) > round(current_sl, 4):
                    logger.info(f"[CHANDELIER ML-WICK] {symbol} SL {current_sl:.4f} -> {new_sl:.4f} (Dinamik Zırh)")
                    matched_pos.stop_loss_price = round(new_sl, 4)
                    await self._update_broker_sl(symbol, matched_pos.target_profit_price, matched_pos.stop_loss_price, matched_pos.market)
                    await self._notify_ui(symbol, matched_pos)
                return

            # === DİNAMİK İZ SÜREN STOP (KÂRA GEÇİNCE) ===
            # Sadece varlık KÂRA GEÇTİĞİNDE (fiyat girişin üstüne çıktığında) izleme başlar.
            if history["high_water_mark"] > entry_price:
                candidate_sl = history["high_water_mark"] * (1.0 - trail_pct)
                # KULLANICI DİREKTİFİ: Kâra geçtiğinde SL yeterince alınan değerin üstüne çıkarılarak iz sürebilir.
                if history["high_water_mark"] > (entry_price * (1.0 + trail_pct)):
                    candidate_sl = max(candidate_sl, entry_price * 1.002) # %0.2 komisyon kurtaran Zararsız Nokta (Break-Even) garantisi!
            else:
                candidate_sl = current_sl # Kâra geçmediyse Başlangıç SL'ini koru.

            # KULLANICI DİREKTİFİ: TIME-DECAY BOGMA MEKANİZMASI (BUY)
            if decay_ratio > 0.0:
                initial_sl_distance = (entry_price * 0.025) if (is_crypto or eff_atr_pct > 2.0) else (entry_price * 0.015)
                initial_sl = entry_price - initial_sl_distance
                time_decay_sl = initial_sl + ((entry_price * 1.001 - initial_sl) * decay_ratio)
                candidate_sl = max(candidate_sl, time_decay_sl)

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

                if round(new_sl, 4) < round(current_sl, 4):
                    logger.info(f"[CHANDELIER ML-WICK] {symbol} SELL SL {current_sl:.4f} -> {new_sl:.4f} (Dinamik Zırh)")
                    matched_pos.stop_loss_price = round(new_sl, 4)
                    await self._update_broker_sl(symbol, matched_pos.target_profit_price, matched_pos.stop_loss_price, matched_pos.market)
                    await self._notify_ui(symbol, matched_pos)
                return

            # === DİNAMİK İZ SÜREN STOP (SELL İÇİN) ===
            low_water = min(current_price, history.get("low_water_mark", current_price))
            if current_price < history.get("low_water_mark", current_price):
                history["low_water_mark"] = current_price
                
            # Sadece varlık KÂRA GEÇTİĞİNDE (fiyat girişin altına düştüğünde) izleme başlar.
            if history.get("low_water_mark", current_price) < entry_price:
                candidate_sl = history.get("low_water_mark", current_price) * (1.0 + trail_pct)
                # KULLANICI DİREKTİFİ (SELL): Kâra geçtiğinde SL yeterince alınan değerin altına inerek iz sürebilir.
                if history.get("low_water_mark", current_price) < (entry_price * (1.0 - trail_pct)):
                    candidate_sl = min(candidate_sl, entry_price * 0.998) # %0.2 komisyon kurtaran Zararsız Nokta (Break-Even) garantisi
            else:
                candidate_sl = current_sl # Kâra geçmediyse Başlangıç SL'ini koru.
            
            # KULLANICI DİREKTİFİ: TIME-DECAY BOGMA MEKANİZMASI (SELL)
            if decay_ratio > 0.0:
                initial_sl_distance = (entry_price * 0.025) if (is_crypto or eff_atr_pct > 2.0) else (entry_price * 0.015)
                initial_sl = entry_price + initial_sl_distance
                time_decay_sl = initial_sl - ((initial_sl - entry_price * 0.999) * decay_ratio)
                candidate_sl = min(candidate_sl, time_decay_sl)

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
            target_broker_name = "BINANCE" if market == "CRYPTO" else "ALPACA"
            broker = get_broker(target_broker_name)
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
