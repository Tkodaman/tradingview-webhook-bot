"""
Piyasa Çalışma Saatleri & Seans Denetleyicisi (Market Hours Validator)
Borsa İstanbul (BIST), NASDAQ/NYSE ve Kripto piyasalarının aktif seans saatlerini denetler.
Piyasa kapalıyken (örneğin BIST akşam/hafta sonu kapalıyken) alım-satım emirlerini ve sahte tetiklemeleri kesin olarak engeller.
"""

from datetime import datetime, timezone, timedelta
from typing import Dict, Any, Tuple

class MarketHoursValidator:
    BIST_SYMBOLS = {
        "THYAO", "ASELS", "BIMAS", "EREGL", "GARAN", "KCHOL", "TUPRS", "SISE", 
        "AKBNK", "YKBNK", "ISCTR", "FROTO", "SAHOL", "PGSUS", "TOASO", "ENKAI", 
        "PETKM", "KOZAL", "SASA", "HEKTS"
    }

    US_SYMBOLS = {
        "NVDA", "AAPL", "MSFT", "AMZN", "GOOGL", "GOOG", "META", "TSLA", "AVGO", "AMD",
        "COST", "NFLX", "TMUS", "ASML", "PEP", "LIN", "CSCO", "ADBE", "TXN", "QCOM",
        "AMAT", "ISRG", "CMCSA", "INTU", "AMGN", "BKNG", "HON", "VRTX", "LRCX", "PANW",
        "MU", "REGN", "ADP", "ADI", "MDLZ", "KLAC", "SNPS", "CDNS", "SBUX", "INTC",
        "GILD", "MELI", "CRWD", "PYPL", "CTAS", "CSX", "MAR", "ORLY", "ABNB", "MNST",
        "NXPI", "WDAY", "FTNT", "AEP", "ROST", "PLTR", "COIN", "MDB", "ARM", "QQQ", "SPY"
    }

    CRYPTO_SYMBOLS = {
        "BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "XRPUSDT", "AVAXUSDT", "DOGEUSDT", "ADAUSDT",
        "LINKUSDT", "NEARUSDT", "SUIUSDT", "PEPEUSDT", "DOTUSDT", "SHIBUSDT", "RENDERUSDT", "FETUSDT",
        "INJUSDT", "APTUSDT", "TAOUSDT", "ARBUSDT", "BTC", "ETH", "SOL", "BNB", "XRP"
    }

    @staticmethod
    def get_turkey_time() -> datetime:
        # UTC + 3
        return datetime.now(timezone.utc) + timedelta(hours=3)

    @classmethod
    def get_market_type(cls, symbol: str) -> str:
        s = symbol.upper()
        if s.startswith("BIST:") or s in cls.BIST_SYMBOLS:
            return "BIST"
        if s.startswith("BINANCE:") or s.startswith("CRYPTO:") or s.endswith("USDT") or (s.endswith("USD") and s != "USD") or s in cls.CRYPTO_SYMBOLS:
            return "CRYPTO"
        clean = s.replace("BIST:", "").replace("NASDAQ:", "").replace("NYSE:", "").replace("BINANCE:", "").replace("USDT", "")
        if clean in cls.BIST_SYMBOLS:
            return "BIST"
        if clean in cls.US_SYMBOLS or s.startswith("NASDAQ:"):
            return "NASDAQ"
        if clean in cls.CRYPTO_SYMBOLS:
            return "CRYPTO"
        return "NASDAQ"

    @classmethod
    def get_market_overview(cls) -> Dict[str, Dict[str, Any]]:
        """Tüm piyasaların (CRYPTO, BIST, NASDAQ) anlık durumunu döndürür"""
        trt = cls.get_turkey_time()
        weekday = trt.weekday()
        current_time_str = trt.strftime("%H:%M")
        current_minute = trt.hour * 60 + trt.minute
        is_weekend = weekday >= 5

        # BIST: Hafta içi 10:00 - 18:05
        bist_open = not is_weekend and (10 * 60 <= current_minute <= 18 * 60 + 5)
        # NASDAQ: Hafta içi 16:30 - 23:00
        nasdaq_open = not is_weekend and (16 * 60 + 30 <= current_minute <= 23 * 60)
        nasdaq_pre = not is_weekend and (11 * 60 <= current_minute < 16 * 60 + 30)

        return {
            "CRYPTO": {
                "market": "CRYPTO",
                "is_open": True,
                "status_badge": "🟢 7/24 PİYASA AÇIK",
                "session_text": "7/24 Kesintisiz Canlı Seans",
                "hours": "7/24",
                "trt_time": current_time_str
            },
            "BIST": {
                "market": "BIST",
                "is_open": bist_open,
                "status_badge": "🟢 CANLI SEANS AÇIK" if bist_open else "🔴 PİYASA KAPALI",
                "session_text": "Hafta İçi 10:00 - 18:05 TSİ" if bist_open else "Seans Dışı (Hafta İçi 10:00 - 18:05 TSİ)",
                "hours": "10:00 - 18:05 TSİ",
                "trt_time": current_time_str
            },
            "NASDAQ": {
                "market": "NASDAQ",
                "is_open": nasdaq_open,
                "is_pre_market": nasdaq_pre,
                "status_badge": "🟢 CANLI SEANS AÇIK" if nasdaq_open else ("🟡 PRE-MARKET" if nasdaq_pre else "🔴 PİYASA KAPALI"),
                "session_text": "Hafta İçi 16:30 - 23:00 TSİ (Wall Street)" if nasdaq_open else "Seans Dışı (Hafta İçi 16:30 - 23:00 TSİ)",
                "hours": "16:30 - 23:00 TSİ",
                "trt_time": current_time_str
            }
        }

    @classmethod
    def is_market_open(cls, symbol: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Dönüş:
        - is_open: bool (Piyasa şu anda aktif işlem saatinde mi?)
        - status_message: str (Piyasa durumu ve çalışma saatleri açıklaması)
        - details: Dict (Seans detayları)
        """
        market = cls.get_market_type(symbol)
        trt = cls.get_turkey_time()
        weekday = trt.weekday()  # 0: Pazartesi, ..., 4: Cuma, 5: Cumartesi, 6: Pazar
        current_time_str = trt.strftime("%H:%M")

        # 1. KRİPTO (24/7 AÇIK)
        if market == "CRYPTO":
            return True, "🟢 Kripto Piyasası 7/24 Açık", {
                "market": "CRYPTO", "is_open": True, "trt_time": current_time_str
            }

        # Hafta Sonu Kontrolü (Cumartesi & Pazar)
        if weekday >= 5:
            day_name = "Cumartesi" if weekday == 5 else "Pazar"
            return False, f"🔴 PİYASA KAPALI: Hafta sonu ({day_name}). İşlem saatleri dışındadır.", {
                "market": market, "is_open": False, "reason": "WEEKEND", "trt_time": current_time_str
            }

        # 2. BORSA İSTANBUL (BIST)
        # Hafta içi 10:00 - 18:05 TRT
        if market == "BIST":
            bist_open_minute = 10 * 60       # 10:00
            bist_close_minute = 18 * 60 + 5  # 18:05
            current_minute = trt.hour * 60 + trt.minute

            if bist_open_minute <= current_minute <= bist_close_minute:
                return True, f"🟢 BIST Seansı Açık ({current_time_str} TRT)", {
                    "market": "BIST", "is_open": True, "trt_time": current_time_str, "hours": "10:00 - 18:05 TRT"
                }
            else:
                return False, f"🔴 BIST KAPALI: Seans saatleri dışındadır (İşlem Saatleri: Hafta İçi 10:00 - 18:05 TRT). Şu an: {current_time_str} TRT", {
                    "market": "BIST", "is_open": False, "reason": "OUTSIDE_HOURS", "trt_time": current_time_str, "hours": "10:00 - 18:05 TRT"
                }

        # 3. ABD BORSALARI (NASDAQ / NYSE)
        # Düzenli Seans: 16:30 - 23:00 TRT (09:30 - 16:00 ET)
        # Pre-Market: 11:00 - 16:30 TRT
        if market == "NASDAQ":
            us_open_minute = 16 * 60 + 30    # 16:30 TRT
            us_close_minute = 23 * 60        # 23:00 TRT
            current_minute = trt.hour * 60 + trt.minute

            if us_open_minute <= current_minute <= us_close_minute:
                return True, f"🟢 NASDAQ / ABD Seansı Açık ({current_time_str} TRT)", {
                    "market": "NASDAQ", "is_open": True, "trt_time": current_time_str, "hours": "16:30 - 23:00 TRT"
                }
            elif (11 * 60) <= current_minute < us_open_minute:
                return False, f"🟡 NASDAQ Pre-Market Açık Ancak Otonom İşlemlere Kapalı ({current_time_str} TRT)", {
                    "market": "NASDAQ", "is_open": False, "session": "PRE_MARKET", "trt_time": current_time_str
                }
            else:
                return False, f"🔴 NASDAQ KAPALI: Seans saatleri dışındadır (İşlem Saatleri: 16:30 - 23:00 TRT). Şu an: {current_time_str} TRT", {
                    "market": "NASDAQ", "is_open": False, "reason": "OUTSIDE_HOURS", "trt_time": current_time_str
                }

        return True, "🟢 Piyasa Açık", {"market": market, "is_open": True}

market_hours_validator = MarketHoursValidator()
