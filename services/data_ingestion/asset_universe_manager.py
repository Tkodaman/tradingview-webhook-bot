import time
import random
from typing import List, Dict

class AssetUniverseManager:
    """
    Dinamik Varlık Havuzu Yöneticisi
    Statik listeler yerine yüzlerce varlık arasından hacim, trend ve LLM/ML
    kriterlerine (simüle edilmiş veya gerçek) uyan "mantıklı" varlıkları hedefe kilitler.
    """
    def __init__(self):
        self.last_rotation_time = 0
        self.rotation_interval_seconds = 90  # 90 saniyede bir — erken sinyali daha hizli yakalar (eskisi 300s)

        # Aktif hedeflenen havuz (Current targets)
        self.active_crypto_targets: List[str] = []
        self.active_bist_targets: List[str] = []
        self.active_nasdaq_targets: List[str] = []

        # Master Universal Lists (Alpaca'nın ŞU AN AKTİF OLARAK desteklediği Kripto varlıkları)
        # Sistem Alpaca'dan "Asset not found" red yememek için Alpaca'nın /v2/assets API'sinden
        # bizzat onaylanmış tüm 33 adet trade edilebilir varlıkla güncellenmiştir.
        self.master_crypto_universe = [
            "BINANCE:BTCUSDT", "BINANCE:ETHUSDT", "BINANCE:SOLUSDT", "BINANCE:DOGEUSDT",
            "BINANCE:AVAXUSDT", "BINANCE:ADAUSDT", "BINANCE:DOTUSDT", "BINANCE:UNIUSDT",
            "BINANCE:SHIBUSDT", "BINANCE:POLUSDT", "BINANCE:AAVEUSDT", "BINANCE:CRVUSDT",
            "BINANCE:GRTUSDT", "BINANCE:BATUSDT", "BINANCE:SUSHIUSDT", "BINANCE:LINKUSDT",
            "BINANCE:BCHUSDT", "BINANCE:LTCUSDT", "BINANCE:XRPUSDT", "BINANCE:YFIUSDT",
            "BINANCE:PEPEUSDT", "BINANCE:WIFUSDT", "BINANCE:RENDERUSDT", "BINANCE:BONKUSDT",
            "BINANCE:ARBUSDT", "BINANCE:ONDOUSDT", "BINANCE:LDOUSDT", "BINANCE:FILUSDT",
            "BINANCE:XTZUSDT", "BINANCE:PAXGUSDT", "CRYPTO:TRUMPUSD", "CRYPTO:SKYUSD",
            "CRYPTO:HYPEUSD",
            # === +5 YENI KRIPTO (Yuksek Momentum & Likidite) ===
            "BINANCE:SUIUSDT",   # SUI - Layer1, kurumsal ilgi yuksek
            "BINANCE:TONUSDT",   # TON - Telegram ekosistemi, hacim patlamasi
            "BINANCE:NEARUSDT",  # NEAR - AI zinciri, guclu momentum
            "BINANCE:JUPUSDT",   # JUP - Solana DEX aggregator, yuksek hacim
            "BINANCE:INJUSDT",   # INJ - DeFi/Cosmos, guvenilir volatilite
        ] # 38 adet - Tam destekli ve likiditesi yuksek Alpaca + Binance Kripto Listesi
        
        self.master_bist_universe = [
            "BIST:THYAO", "BIST:ASELS", "BIST:EREGL", "BIST:TUPRS", "BIST:KCHOL",
            "BIST:GARAN", "BIST:AKBNK", "BIST:SISE", "BIST:PETKM", "BIST:BIMAS",
            "BIST:YKBNK", "BIST:SAHOL", "BIST:ISCTR", "BIST:ENKAI", "BIST:PGSUS",
            "BIST:FROTO", "BIST:TOASO", "BIST:TCELL", "BIST:TTKOM", "BIST:EKGYO",
            "BIST:KOZAL", "BIST:KRDMD", "BIST:HEKTS", "BIST:SASA", "BIST:ASTOR",
            "BIST:ALFAS", "BIST:CWENE", "BIST:GESAN", "BIST:EUPWR", "BIST:KONTR"
        ] # 30 assets

        self.master_nasdaq_universe = [
            # Top-Tier Big Tech & Growth
            "NASDAQ:NVDA", "NASDAQ:AAPL", "NASDAQ:MSFT", "NASDAQ:AMZN", "NASDAQ:GOOGL",
            "NASDAQ:GOOG", "NASDAQ:META", "NASDAQ:TSLA", "NASDAQ:AVGO", "NASDAQ:AMD",
            "NASDAQ:COST", "NASDAQ:NFLX", "NASDAQ:TMUS", "NASDAQ:ASML", "NASDAQ:PEP",
            "NASDAQ:LIN", "NASDAQ:CSCO", "NASDAQ:ADBE", "NASDAQ:TXN", "NASDAQ:QCOM",
            
            # High Momentum & AI / Chips
            "NYSE:VRT", "NYSE:EME", "NYSE:GLW", # User-requested targets
            "NASDAQ:AMAT", "NASDAQ:ISRG", "NASDAQ:CMCSA", "NASDAQ:INTU", "NASDAQ:AMGN",
            "NASDAQ:BKNG", "NASDAQ:HON", "NASDAQ:VRTX", "NASDAQ:LRCX", "NASDAQ:PANW",
            "NASDAQ:MU", "NASDAQ:REGN", "NASDAQ:ADP", "NASDAQ:ADI", "NASDAQ:MDLZ",
            "NASDAQ:KLAC", "NASDAQ:SNPS", "NASDAQ:CDNS", "NASDAQ:SBUX", "NASDAQ:INTC",
            "NASDAQ:SMCI", "NASDAQ:ARM", "NASDAQ:MRVL", "NYSE:DELL", "NYSE:HPE", 
            "NASDAQ:WDC", "NASDAQ:STX", "NYSE:ANET", "NYSE:AI", "NYSE:TSM",
            
            # Cloud, Cybersecurity & Software
            "NASDAQ:CRWD", "NASDAQ:PYPL", "NASDAQ:CTAS", "NASDAQ:CSX", "NASDAQ:MAR",
            "NASDAQ:ORLY", "NASDAQ:ABNB", "NASDAQ:MNST", "NASDAQ:NXPI", "NASDAQ:WDAY",
            "NASDAQ:FTNT", "NASDAQ:AEP", "NASDAQ:ROST", "NYSE:PLTR", "NASDAQ:MDB",
            "NASDAQ:ZS", "NASDAQ:DDOG", "NYSE:CRM", "NYSE:NOW", "NASDAQ:TEAM", 
            "NYSE:NET", "NYSE:SNOW", "NYSE:DOCN", "NASDAQ:OKTA", "NASDAQ:ZM", 
            "NYSE:TWLO", "NASDAQ:ROKU", "NYSE:U", "NASDAQ:TTD", "NYSE:PATH",
            
            # FinTech, E-Commerce & Retail
            "NASDAQ:MELI", "NYSE:SHOP", "NYSE:SQ", "NYSE:SPOT", "NYSE:RBLX",
            "NASDAQ:SOFI", "NASDAQ:AFRM", "NYSE:V", "NYSE:MA", "NYSE:AXP",
            "NYSE:JPM", "NYSE:BAC", "NYSE:GS", "NYSE:MS", "NYSE:BLK",
            "NYSE:WMT", "NYSE:TGT", "NYSE:HD", "NYSE:MCD", "NYSE:NKE",
            "NASDAQ:LULU", "NYSE:DIS", "NYSE:SONY", "NYSE:RACE", "NYSE:UBER",
            
            # Crypto-Adjacent & Memes
            "NASDAQ:COIN", "NASDAQ:MSTR", "NASDAQ:MARA", "NASDAQ:RIOT", "NASDAQ:CLSK",
            "NASDAQ:HOOD", "NASDAQ:IREN", "NASDAQ:CIFR", "NASDAQ:HUT", "NASDAQ:GME",
            "NYSE:AMC", "NYSE:RDDT",

            # High-Volatility & Leveraged ETFs (Yüksek beta / erken fırsat)
            "AMEX:SOXL",   # SOXL - 3x Leveraged Semiconductor ETF (çok oynak)
            "AMEX:TQQQ",   # TQQQ - 3x NASDAQ Leveraged ETF
            "AMEX:LABU",   # LABU - 3x Leveraged Biotech ETF
            "AMEX:FNGU",   # FNGU - 3x Big Tech ETF

            # Telecom & Value (Düşük fiyat, yüksek ivme potansiyeli)
            "NYSE:NOK",    # Nokia - Telecom/5G, düşük fiyatlı geniş hacim
            "NASDAQ:ERIC", # Ericsson - 5G Telecom rakibi
            
            # Biotech, Pharma & Health
            "NASDAQ:GILD", "NYSE:LLY", "NYSE:NVO", "NYSE:PFE", "NYSE:MRK",
            "NYSE:ABBV", "NYSE:JNJ", "NASDAQ:BIIB", "NASDAQ:MRNA", "NASDAQ:ILMN",
            "NYSE:UNH", "NYSE:PG",
            
            # EV, Auto, Energy & Industrials
            "NASDAQ:RIVN", "NASDAQ:LCID", "NYSE:F", "NYSE:GM", "NYSE:XOM", 
            "NYSE:CVX", "NYSE:OXY", "NASDAQ:ENPH", "NASDAQ:FSLR", "NASDAQ:SEDG",
            "NASDAQ:SPWR", "NYSE:BA", "NYSE:CAT", "NYSE:GE", "NYSE:LMT",
            "NYSE:RTX", "NYSE:NOC", "NYSE:GD",
            
            # Indexes / ETFs (For Macro Baseline)
            "NASDAQ:QQQ", "AMEX:SPY", "AMEX:DIA", "AMEX:IWM",

            # === +5 YENI NASDAQ (Yuksek Momentum & Buyume) ===
            "NASDAQ:HIMS",   # HIMS - Saglik/wellness, guclu momentum trendi
            "NASDAQ:APP",    # AppLovin - AI reklam motoru, 2024-25 en iyi hisse
            "NASDAQ:SOUN",   # SoundHound AI - AI ses teknolojisi, spekulatif yuksek beta
            "NYSE:JOBY",     # JOBY Aviation - eVTOL/ucen taksi, buyuk kurumsal ilgi
            "NYSE:WOLF",     # Wolfspeed - Sic karbur yari iletken, EV/AI chip
        ] # 165+ Mega & Volatile US Stocks

        self.target_crypto_count = 38
        self.target_bist_count = 20
        self.target_nasdaq_count = 165  # Tüm universe izlenir

        self._force_rotation()

    def _early_entry_score(self, ticker: str) -> float:
        """
        STANDART ÇOKLU FAKTÖR ROTASYON SKORU

        Felsefe: Hiçbir RSI bandına ayrıcalık tanıma. Tüm varlıklar
        hacim, CMF, EMA, ADX ve fiyat momentumuna göre adil yarışır.
        Bu skor yalnızca hangi varlıkların AKTIF listeye gireceğini belirler.
        """
        try:
            from services.data_ingestion.tradingview_live_client import tradingview_live_client
            sym = ticker.split(":")[-1]
            cached = {
                **tradingview_live_client.cached_us_data,
                **tradingview_live_client.cached_tr_data,
                **tradingview_live_client.cached_crypto_data
            }
            d = cached.get(sym)
            if not d:
                return 50.0  # Veri yoksa nötr puan ver (listeden çıkarmak yerine)

            rsi        = float(d.get("rsi", 50))
            vol_ratio  = float(d.get("volume_ratio", 1.0) or 1.0)
            chg        = float(d.get("change_pct", 0.0))
            ema_gc     = bool(d.get("ema_golden_cross", False))
            cmf        = float(d.get("cmf", 0.0))
            adx        = float(d.get("adx", 20.0))
            macd       = float(d.get("macd", 0.0))
            supertrend = bool(d.get("supertrend_bullish", True))

            score = 50.0  # Taban puan — her varlık 50'den başlar

            # ── 1. RSI: Tüm güçlü bantlar ödüllendirilir ─────────────
            # Aşırı satım (<30) ve çok güçlü trend (>70) hariç her bant adil
            if rsi >= 60.0:   score += 15.0   # Güçlü trend
            elif rsi >= 50.0: score += 10.0   # Pozitif bölge
            elif rsi >= 35.0: score +=  5.0   # Dip yakını / toparlanma
            elif rsi < 25.0:  score -= 10.0   # Aşırı baskı altında
            if rsi > 78.0:    score -= 15.0   # Sadece aşırı şişmiş ceza al

            # ── 2. Hacim: Her türlü hacim artışı ödüllenir ───────────
            if vol_ratio >= 3.0:   score += 30.0  # Balina dalgası
            elif vol_ratio >= 1.5: score += 20.0  # Güçlü hacim
            elif vol_ratio >= 1.0: score += 10.0  # Normal üstü
            elif vol_ratio < 0.5:  score -= 10.0  # Çok düşük hacim

            # ── 3. MACD ve EMA ───────────────────────────────────────
            if macd >= 0.0: score += 8.0
            if ema_gc:      score += 12.0
            elif supertrend: score += 5.0

            # ── 4. CMF: Kurumsal para girişi ─────────────────────────
            if cmf > 0.15:    score += 15.0
            elif cmf > 0.05:  score += 8.0
            elif cmf < -0.10: score -= 10.0

            # ── 5. ADX: Trend gücü ───────────────────────────────────
            if adx >= 30.0:    score += 10.0  # Güçlü trend aktif
            elif adx >= 20.0:  score +=  5.0  # Trend başlıyor

            # ── 6. Fiyat momentumu ───────────────────────────────────
            if chg >= 2.0:   score += 10.0
            elif chg >= 0.5: score +=  5.0
            elif chg < -3.0: score -= 10.0  # Serbest düşüş

            return score

        except Exception:
            return 50.0

    # Geriye dönük uyumluluk için alias
    def _momentum_score(self, ticker: str) -> float:
        return self._early_entry_score(ticker)

    def _early_alert_watchlist(self) -> list:
        """
        Her rotasyonda tüm master universe'i tarayarak ERKEN sinyal veren
        sembolleri tespit et ve log'a yaz. Henüz aktif listeye girmemiş
        olanları da yakalar — asıl değer buradan geliyor.
        """
        from core.logger import logger
        all_candidates = []

        for ticker in (self.master_crypto_universe +
                       self.master_bist_universe +
                       self.master_nasdaq_universe):
            sc = self._early_entry_score(ticker)
            if sc >= 55.0:
                all_candidates.append((ticker.split(":")[-1], round(sc, 1)))

        all_candidates.sort(key=lambda x: x[1], reverse=True)

        if all_candidates:
            top5 = all_candidates[:5]
            logger.info(
                "[ERKEN RADAR] Top-5 erken giris adayi: "
                + " | ".join([f"{s}(skor={sc})" for s, sc in top5])
            )
        return all_candidates

    def _force_rotation(self):
        """
        ERKEN TESPITCI Oncelikli Rotasyon
        Yukseldikten sonra degil — yukselmeden ONCE olan varliklari one alir.
        Her 90 saniyede bir calisir.
        """
        from core.logger import logger
        self.last_rotation_time = time.time()

        def sort_by_early_entry(universe: list) -> list:
            try:
                scored = [(t, self._early_entry_score(t)) for t in universe]
                scored.sort(key=lambda x: x[1], reverse=True)
                return [t for t, _ in scored]
            except Exception:
                shuffled = list(universe)
                random.shuffle(shuffled)
                return shuffled

        sorted_crypto = sort_by_early_entry(self.master_crypto_universe)
        self.active_crypto_targets = sorted_crypto[:self.target_crypto_count]

        sorted_bist = sort_by_early_entry(self.master_bist_universe)
        self.active_bist_targets = sorted_bist[:self.target_bist_count]

        sorted_nasdaq = sort_by_early_entry(self.master_nasdaq_universe)
        self.active_nasdaq_targets = sorted_nasdaq[:self.target_nasdaq_count]

        # Benchmark'larin her zaman izlenmesi
        if "BINANCE:BTCUSDT" not in self.active_crypto_targets:
            self.active_crypto_targets.append("BINANCE:BTCUSDT")
        if "BIST:XU100" not in self.active_bist_targets:
            self.active_bist_targets.append("BIST:XU100")
        if "NASDAQ:QQQ" not in self.active_nasdaq_targets:
            self.active_nasdaq_targets.append("NASDAQ:QQQ")

        # Erken uyari radar taramasi — top-5'i logla
        self._early_alert_watchlist()

    def get_active_tickers(self) -> Dict[str, List[str]]:
        now = time.time()
        if now - self.last_rotation_time > self.rotation_interval_seconds:
            self._force_rotation()

        return {
            "CRYPTO": self.active_crypto_targets,
            "BIST": self.active_bist_targets,
            "NASDAQ": self.active_nasdaq_targets
        }

asset_universe_manager = AssetUniverseManager()

