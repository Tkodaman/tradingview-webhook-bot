"""
SUI/TRY - Manuel Portföy İzleyici & Dip Alarm Motoru
=====================================================
Görev 1: SL Alarmı   — Fiyat tanımlı stop seviyesine düşünce sesli alarm + log.
Görev 2: Soğuma/Dip  — Fiyat yerel dipten %N toparlanmaya başlarsa "TRENE BİN" sinyali üretir.
Görev 3: Periyodik    — Her 60 saniyede fiyatı çeker, durumu raporlar.

Çalıştırmak için ayrı bir terminal:
  python -m services.monitors.sui_dip_alarm
"""

import time, json, requests, threading
from datetime import datetime
from zoneinfo import ZoneInfo

TRT = ZoneInfo("Europe/Istanbul")

# ─── KONFIGÜRASYON ────────────────────────────────────────────────────────────
SYMBOL_USDT  = "SUIUSDT"
SYMBOL_TRY   = "USDTTRY"

# Mevcut pozisyon
ENTRY_PRICE  = 58.91      # TRY
TOTAL_COST   = 43_936.0   # TRY

# Stop-Loss seviyesi: Girişin %7 altı → inat yok, çık.
HARD_SL_PCT  = -7.0       # %  (bu seviyeye düşerse alarm + çık önerisi)
SL_PRICE     = ENTRY_PRICE * (1 + HARD_SL_PCT / 100)  # ~54.78 TRY

# Soğuma/Dip Tespiti
# Fiyat yerel dipten %2.5 yukarı döndüğünde ve RSI proxy (24h-low baz alınır)
# aşağı yorgunluğunu bitirdiğinde "DIP_ENTRY" sinyali.
DIP_RECOVER_PCT = 2.5     # Dipten bu kadar toparlanınca giriş sinyali ver
DIP_COOLDOWN_H  = 1.0     # En son dipten bu kadar saat geçmiş olmalı

# Alarm
CHECK_INTERVAL_SEC = 60   # Kaç saniyede bir kontrol

# ─── DURUM ───────────────────────────────────────────────────────────────────
_state = {
    "local_low"       : None,   # Gözlemlenen en düşük TRY fiyatı
    "local_low_time"  : None,
    "sl_alarm_fired"  : False,
    "dip_signal_fired": False,
    "last_price"      : None,
}


def _get_prices() -> dict | None:
    try:
        r1 = requests.get(
            f"https://api.binance.com/api/v3/ticker/24hr?symbol={SYMBOL_USDT}",
            timeout=6
        ).json()
        r2 = requests.get(
            f"https://api.binance.com/api/v3/ticker/price?symbol={SYMBOL_TRY}",
            timeout=6
        ).json()
        usdt_try   = float(r2["price"])
        sui_usdt   = float(r1["lastPrice"])
        sui_try    = sui_usdt * usdt_try
        low_24h    = float(r1["lowPrice"]) * usdt_try
        high_24h   = float(r1["highPrice"]) * usdt_try
        chg_pct    = float(r1["priceChangePercent"])
        return {
            "sui_try"  : round(sui_try, 3),
            "low_24h"  : round(low_24h, 3),
            "high_24h" : round(high_24h, 3),
            "chg_pct"  : round(chg_pct, 2),
            "usdt_try" : round(usdt_try, 2),
            "ts"       : time.time(),
        }
    except Exception as e:
        print(f"[HATA] Fiyat çekilemedi: {e}")
        return None


def _beep_alarm(freq: int = 1000, times: int = 10):
    """Windows sesli uyarı."""
    def _play():
        try:
            import winsound
            for _ in range(times):
                winsound.Beep(freq, 400)
                time.sleep(0.3)
        except Exception:
            pass
    threading.Thread(target=_play, daemon=True).start()


def _log(tag: str, msg: str, level: str = "INFO"):
    import sys
    now = datetime.now(TRT).strftime("%H:%M:%S")
    pfx = {"INFO": "[i]", "WARN": "[!]", "ALARM": "[ALARM]", "SIGNAL": "[SIGNAL]"}.get(level, "[ ]")
    line = f"[{now}] {pfx} [{tag}] {msg}"
    sys.stdout.buffer.write((line + "\n").encode("utf-8", "replace"))


def _check(prices: dict):
    sui   = prices["sui_try"]
    low   = prices["low_24h"]
    now_t = prices["ts"]

    pnl_pct = ((sui - ENTRY_PRICE) / ENTRY_PRICE) * 100
    pnl_tl  = round((sui - ENTRY_PRICE) / ENTRY_PRICE * TOTAL_COST, 0)

    _log("SUI", f"Fiyat: {sui:.3f} TRY  |  PnL: %{pnl_pct:.2f} ({pnl_tl:+.0f} TRY)  |  24h Değ: %{prices['chg_pct']}")

    # ── GÖREV 1: HARD SL ALARMI ───────────────────────────────────────────────
    if sui <= SL_PRICE and not _state["sl_alarm_fired"]:
        _state["sl_alarm_fired"] = True
        _beep_alarm(freq=400, times=15)
        _log("🚨 SL ALARM", (
            f"SUI {sui:.3f} TRY → SL seviyesi {SL_PRICE:.2f} TRY aşıldı! "
            f"PnL: %{pnl_pct:.2f} ({pnl_tl:+.0f} TRY). "
            f"ÖNERİ: Pozisyonu kapat, zarar büyümesin."
        ), level="ALARM")
    elif sui > SL_PRICE and _state["sl_alarm_fired"]:
        # Fiyat geri döndü, alarmı resetle
        _state["sl_alarm_fired"] = False
        _log("SL", "Fiyat SL üzerine döndü. Alarm sıfırlandı.", level="INFO")

    # ── GÖREV 2: YEREL DİP TAKİBİ & TRENE BİN SİNYALİ ───────────────────────
    # Yerel dibi güncelle
    if _state["local_low"] is None or sui < _state["local_low"]:
        _state["local_low"]      = sui
        _state["local_low_time"] = now_t
        _state["dip_signal_fired"] = False  # Yeni dip → sinyali resetle
        _log("DIP", f"Yeni yerel dip: {sui:.3f} TRY", level="WARN")

    # Dipten toparlanma kontrolü
    if _state["local_low"] is not None and not _state["dip_signal_fired"]:
        recover_pct = ((sui - _state["local_low"]) / _state["local_low"]) * 100
        hours_since_low = (now_t - _state["local_low_time"]) / 3600.0

        if recover_pct >= DIP_RECOVER_PCT and hours_since_low >= DIP_COOLDOWN_H:
            _state["dip_signal_fired"] = True
            _beep_alarm(freq=1500, times=8)
            _log("🚀 DIP ENTRY", (
                f"SUI dip ({_state['local_low']:.3f} TRY) sonrası %{recover_pct:.2f} toparlandı! "
                f"Dip'ten bu yana {hours_since_low:.1f} saat geçti. "
                f"GÜNCEL: {sui:.3f} TRY | SL: {SL_PRICE:.2f} TRY. "
                f"BU SEFER AŞAĞIDAN BİN, treni sondan değil altından yakala."
            ), level="SIGNAL")

    # ── GÖREV 3: DURUM RAPORU ─────────────────────────────────────────────────
    local_low_str = f"{_state['local_low']:.3f}" if _state["local_low"] else "—"
    _log("DURUM", (
        f"Entry: {ENTRY_PRICE} TRY | SL: {SL_PRICE:.2f} TRY | "
        f"Yerel Dip: {local_low_str} TRY | "
        f"24h Düşük: {low:.3f} TRY"
    ))


def run():
    _log("SUI-ALARM", f"İzleme başladı. Entry={ENTRY_PRICE} TRY | Hard SL={SL_PRICE:.2f} TRY (%{HARD_SL_PCT})", level="INFO")
    _log("SUI-ALARM", f"Dip Giriş Sinyali: Yerel dipten %{DIP_RECOVER_PCT} toparlanma + {DIP_COOLDOWN_H}s bekleme", level="INFO")

    while True:
        prices = _get_prices()
        if prices:
            _check(prices)
            _state["last_price"] = prices["sui_try"]
        time.sleep(CHECK_INTERVAL_SEC)


if __name__ == "__main__":
    run()
