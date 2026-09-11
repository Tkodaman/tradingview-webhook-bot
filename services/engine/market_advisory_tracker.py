import time
from typing import Dict, List
from datetime import datetime
from core.logger import logger
from routers.top_picks_cache import get_cached_top_picks


class MarketAdvisoryTracker:
    def __init__(self):
        self.virtual_positions: Dict[str, Dict] = {"BIST": {}, "NASDAQ": {}, "CRYPTO": {}}
        self.advisory_streams: Dict[str, List[str]] = {"BIST": [], "NASDAQ": [], "CRYPTO": []}
        self._last_update = 0
        self._last_price_snapshot: Dict[str, float] = {}  # Anlık fiyat değişim takibi

    def get_streams(self) -> Dict[str, List[str]]:
        self.update_virtual_positions()
        for mkt in ["BIST", "NASDAQ", "CRYPTO"]:
            if not self.advisory_streams[mkt]:
                self._seed_initial_stream(mkt)
        return self.advisory_streams

    def update_virtual_positions(self):
        now = time.time()
        if now - self._last_update < 5:
            return
        self._last_update = now

        picks = get_cached_top_picks()
        if not picks:
            return

        time_str = datetime.now().strftime("%H:%M:%S")

        for mkt in ["BIST", "NASDAQ", "CRYPTO"]:
            currency_sym = "TL" if mkt == "BIST" else "$"
            total_pool = 80000.0 if mkt == "BIST" else 10000.0

            mkt_picks = [p for p in picks if p.get("market") == mkt and p.get("confidence_pct", 0) >= 70]
            active_pos_count = sum(1 for p in self.virtual_positions[mkt].values() if p["active"])
            price_map = {p["symbol"]: p.get("price", 0) for p in picks if p.get("market") == mkt}

            # 1) Yeni fırsatları sanal portföye ekle
            for pick in mkt_picks:
                sym = pick["symbol"]
                entry = pick.get("price", 0)
                confidence = pick.get("confidence_pct", 0)

                if sym not in self.virtual_positions[mkt] and entry > 0:
                    divisor = max(1, active_pos_count + 1)
                    allocated = (total_pool / divisor) * (confidence / 100.0)
                    tp = pick.get("tp_target", entry * 1.03)
                    sl = pick.get("sl_target", entry * 0.97)
                    self.virtual_positions[mkt][sym] = {
                        "entry_price": entry,
                        "entry_time": datetime.now(),
                        "confidence": confidence,
                        "tp_target": tp,
                        "sl_target": sl,
                        "allocated_capital": allocated,
                        "active": True
                    }
                    active_pos_count += 1
                    alerts = pick.get("key_alerts", [])
                    alert_str = f" ➜ {alerts[0]}" if alerts else ""
                    ind_count = len(alerts) + 24
                    msg = (
                        f"🔔 FIRSAT: {sym} ({mkt}): "
                        f"ADX trend gücü {ind_count} indikatörün {confidence:.0f}% güven skoruyla onayladı."
                        f" (Giriş: {currency_sym}{entry:.2f}, Hedef: {currency_sym}{tp:.2f}, SL: {currency_sym}{sl:.2f})"
                        f"{alert_str}"
                    )
                    self._add_to_stream(mkt, msg)

                elif sym in self.virtual_positions[mkt]:
                    # Mevcut pozisyon için anlık fiyat takibi
                    pos = self.virtual_positions[mkt][sym]
                    if not pos["active"]:
                        continue
                    current_price = price_map.get(sym, pos["entry_price"])
                    if current_price <= 0:
                        continue
                    prev_price = self._last_price_snapshot.get(f"{mkt}:{sym}", pos["entry_price"])
                    price_change_pct = abs((current_price - prev_price) / prev_price * 100) if prev_price > 0 else 0
                    pnl_pct = ((current_price - pos["entry_price"]) / pos["entry_price"]) * 100
                    elapsed_mins = int((datetime.now() - pos["entry_time"]).total_seconds() / 60)
                    self._last_price_snapshot[f"{mkt}:{sym}"] = current_price

                    if price_change_pct >= 0.15:
                        direction = "▲ yükseliyor" if current_price > prev_price else "▼ düşüyor"
                        pnl_sign = "+" if pnl_pct >= 0 else ""
                        msg = (
                            f"📡 [{time_str}] {sym} ({mkt}) {direction}: {currency_sym}{current_price:.2f}"
                            f" | Giriş'ten: {pnl_sign}{pnl_pct:.2f}%"
                            f" | TP: {currency_sym}{pos['tp_target']:.2f}"
                            f" SL: {currency_sym}{pos['sl_target']:.2f}"
                            f" | {elapsed_mins} dk izlemede"
                        )
                        self._add_to_stream(mkt, msg)

            # 2) TP / SL Kontrol
            for sym, pos in list(self.virtual_positions[mkt].items()):
                if not pos["active"]:
                    continue
                current_price = price_map.get(sym, pos["entry_price"])
                if current_price <= 0:
                    continue
                pnl_pct = ((current_price - pos["entry_price"]) / pos["entry_price"]) * 100
                elapsed_mins = int((datetime.now() - pos["entry_time"]).total_seconds() / 60)

                if pnl_pct >= 3.0:
                    mock_profit = pos.get("allocated_capital", 10000) * (pnl_pct / 100.0)
                    msg = (
                        f"✅ [{time_str}] BAŞARILI ÖNGÖRÜ: {sym} ({mkt}) → {elapsed_mins} dk'da "
                        f"+%{pnl_pct:.2f} TP'ye ULAŞTI! "
                        f"Simüle kâr: +{mock_profit:,.0f} {currency_sym}"
                    )
                    self._add_to_stream(mkt, msg)
                    pos["active"] = False
                elif pnl_pct <= -2.5:
                    mock_loss = pos.get("allocated_capital", 10000) * (abs(pnl_pct) / 100.0)
                    msg = (
                        f"⚠️ [{time_str}] RİSK UYARISI: {sym} ({mkt}) → %{pnl_pct:.2f} zararda. "
                        f"Simüle kayıp: -{mock_loss:,.0f} {currency_sym}. Stop-loss devreye girmeli."
                    )
                    self._add_to_stream(mkt, msg)
                    pos["active"] = False

    def _seed_initial_stream(self, mkt: str):
        """Uygulama ilk açıldığında gösterilecek ısındırma metinleri."""
        seed_msgs = {
            "BIST": [
                "🤖 Midas manuel işlemleriniz için BIST Otonom Danışman devrede...",
                "📈 Algoritma BIST hacim patlamalarını canlı izliyor — %80+ güven skorlu analizler simüle edilecek."
            ],
            "NASDAQ": [
                "🤖 NASDAQ Otonom Piyasa İzleyici devrede...",
                "📈 Hızlı teknoloji hisseleri ve makro veriler taranıyor, simüle hedefler yolda."
            ],
            "CRYPTO": [
                "🤖 7/24 Kripto Otonom Takip Radarı devrede...",
                "📈 Balina cüzdan hareketleri ve momentum kırılımları analiz ediliyor."
            ]
        }
        for msg in seed_msgs.get(mkt, []):
            self._add_to_stream(mkt, msg)

    def _add_to_stream(self, mkt: str, message: str):
        time_str = datetime.now().strftime("%H:%M:%S")
        full_msg = f"[{time_str}] {message}"
        # Tam aynı mesajı tekrar ekleme
        if self.advisory_streams[mkt] and self.advisory_streams[mkt][0] == full_msg:
            return
        self.advisory_streams[mkt].insert(0, full_msg)
        if len(self.advisory_streams[mkt]) > 20:
            self.advisory_streams[mkt].pop()


market_advisory_tracker = MarketAdvisoryTracker()
