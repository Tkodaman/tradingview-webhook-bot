"""
Korelasyon Filtresi — Portfoy Korelasyon Yonetimi
Kripto gibi yuksek korelasyonlu varliklarda ayni anda birden fazla pozisyon acilmasini engeller.
Kural: Ayni korelasyon grubundan max 1 pozisyon (kripto) veya max 2 pozisyon (hisse) acik olabilir.
"""
from typing import Optional
from core.logger import logger


# Korelasyon Gruplari
CORRELATION_GROUPS = {
    "CRYPTO_MAJOR": {
        "symbols": ["BTCUSDT", "ETHUSDT", "SOLUSDT", "BNBUSDT", "AVAXUSDT", "BTCUSD", "ETHUSD", "SOLUSD", "BNBUSD"],
        "max_positions": 1,
        "description": "Buyuk Kripto (BTC/ETH/SOL/BNB) — Korelasyon >0.85"
    },
    "CRYPTO_ALT": {
        "symbols": ["XRPUSDT", "ADAUSDT", "DOTUSDT", "LINKUSDT", "MATICUSDT", "LTCUSDT", "XRPUSD", "ADAUSD"],
        "max_positions": 1,
        "description": "Alternatif Kripto — Korelasyon ~0.75"
    },
    "US_TECH": {
        "symbols": ["AAPL", "MSFT", "NVDA", "AMD", "GOOGL", "GOOG", "META", "AMZN", "TSLA"],
        "max_positions": 2,
        "description": "ABD Buyuk Teknoloji — Korelasyon ~0.70"
    },
    "US_FINANCE": {
        "symbols": ["JPM", "BAC", "GS", "MS", "C", "WFC", "V", "MA"],
        "max_positions": 1,
        "description": "ABD Finans Sektoru — Korelasyon ~0.65"
    },
    "US_SEMI": {
        "symbols": ["NVDA", "AMD", "INTC", "QCOM", "MU", "TSM", "AMAT", "LRCX"],
        "max_positions": 1,
        "description": "Yari Iletken Sektoru — Korelasyon ~0.80"
    },
}


class CorrelationFilter:
    """
    Portfoy korelasyon filtresi.
    Ayni korelasyon grubundan fazla pozisyon acilmasini engeller.
    """

    def get_group_for_symbol(self, symbol: str) -> Optional[str]:
        """Bir sembolun hangi korelasyon grubuna ait oldugunu dondur."""
        sym_upper = symbol.upper()
        for group_name, group_data in CORRELATION_GROUPS.items():
            if sym_upper in [s.upper() for s in group_data["symbols"]]:
                return group_name
        return None

    def check(self, symbol: str, open_positions: list) -> tuple[bool, str]:
        """
        Sembol icin pozisyon acilip acilmayacagini kontrol et.
        Donus: (gecebilir_mi: bool, sebep: str)
        """
        group_name = self.get_group_for_symbol(symbol)

        if group_name is None:
            # Tanimsiz grup — izin ver
            return True, ""

        group_data = CORRELATION_GROUPS[group_name]
        max_allowed = group_data["max_positions"]

        # Ayni grupta kac acik pozisyon var?
        open_in_group = []
        for pos in open_positions:
            pos_sym = getattr(pos, "symbol", "").upper()
            group_syms = [s.upper() for s in group_data["symbols"]]
            if pos_sym in group_syms and getattr(pos, "status", "") == "OPEN":
                open_in_group.append(pos_sym)

        if len(open_in_group) >= max_allowed:
            reason = (
                f"KORELASYON BLOKAJI: {group_name} grubunda zaten {len(open_in_group)}/{max_allowed} pozisyon acik "
                f"({', '.join(open_in_group)}). {group_data['description']}. "
                f"Yeni {symbol} girisi engellendi."
            )
            logger.info(f"[CORRELATION FILTER] {symbol} blokajda. Grup: {group_name} | Acik: {open_in_group}")
            return False, reason

        return True, ""

    def get_portfolio_correlation_report(self, open_positions: list) -> dict:
        """Portfoy korelasyon durumu raporu."""
        report = {}
        for group_name, group_data in CORRELATION_GROUPS.items():
            group_syms = [s.upper() for s in group_data["symbols"]]
            in_group = [
                getattr(p, "symbol", "")
                for p in open_positions
                if getattr(p, "symbol", "").upper() in group_syms
                and getattr(p, "status", "") == "OPEN"
            ]
            if in_group:
                report[group_name] = {
                    "open": in_group,
                    "count": len(in_group),
                    "max": group_data["max_positions"],
                    "at_limit": len(in_group) >= group_data["max_positions"]
                }
        return report


correlation_filter = CorrelationFilter()
