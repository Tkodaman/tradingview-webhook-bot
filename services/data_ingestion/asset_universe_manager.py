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
        self.rotation_interval_seconds = 3600  # Saat başı rotasyon (Öntanımlı)

        # Aktif hedeflenen havuz (Current targets)
        self.active_crypto_targets: List[str] = []
        self.active_bist_targets: List[str] = []
        self.active_nasdaq_targets: List[str] = []

        # Master Universal Lists (Alpaca'nın şu an desteklediği sınırlı kripto varlıkları)
        # Sistem sürekli Alpaca'dan red yemesin diye sadece %100 desteklenenler eklendi
        self.master_crypto_universe = [
            "BINANCE:BTCUSDT", "BINANCE:ETHUSDT", "BINANCE:BCHUSDT", 
            "BINANCE:LTCUSDT", "BINANCE:LINKUSDT"
        ] # Sadece Alpaca destekli varlıklar
        
        self.master_bist_universe = [
            "BIST:THYAO", "BIST:ASELS", "BIST:EREGL", "BIST:TUPRS", "BIST:KCHOL",
            "BIST:GARAN", "BIST:AKBNK", "BIST:SISE", "BIST:PETKM", "BIST:BIMAS",
            "BIST:YKBNK", "BIST:SAHOL", "BIST:ISCTR", "BIST:ENKAI", "BIST:PGSUS",
            "BIST:FROTO", "BIST:TOASO", "BIST:TCELL", "BIST:TTKOM", "BIST:EKGYO",
            "BIST:KOZAL", "BIST:KRDMD", "BIST:HEKTS", "BIST:SASA", "BIST:ASTOR",
            "BIST:ALFAS", "BIST:CWENE", "BIST:GESAN", "BIST:EUPWR", "BIST:KONTR"
        ] # 30 assets

        self.master_nasdaq_universe = [
            "NASDAQ:NVDA", "NASDAQ:AAPL", "NASDAQ:MSFT", "NASDAQ:AMZN", "NASDAQ:GOOGL",
            "NASDAQ:GOOG", "NASDAQ:META", "NASDAQ:TSLA", "NASDAQ:AVGO", "NASDAQ:AMD",
            "NASDAQ:COST", "NASDAQ:NFLX", "NASDAQ:TMUS", "NASDAQ:ASML", "NASDAQ:PEP",
            "NASDAQ:LIN", "NASDAQ:CSCO", "NASDAQ:ADBE", "NASDAQ:TXN", "NASDAQ:QCOM",
            "NASDAQ:AMAT", "NASDAQ:ISRG", "NASDAQ:CMCSA", "NASDAQ:INTU", "NASDAQ:AMGN",
            "NASDAQ:BKNG", "NASDAQ:HON", "NASDAQ:VRTX", "NASDAQ:LRCX", "NASDAQ:PANW",
            "NASDAQ:MU", "NASDAQ:REGN", "NASDAQ:ADP", "NASDAQ:ADI", "NASDAQ:MDLZ",
            "NASDAQ:KLAC", "NASDAQ:SNPS", "NASDAQ:CDNS", "NASDAQ:SBUX", "NASDAQ:INTC",
            "NASDAQ:GILD", "NASDAQ:MELI", "NASDAQ:CRWD", "NASDAQ:PYPL", "NASDAQ:CTAS",
            "NASDAQ:CSX", "NASDAQ:MAR", "NASDAQ:ORLY", "NASDAQ:ABNB", "NASDAQ:MNST",
            "NASDAQ:NXPI", "NASDAQ:WDAY", "NASDAQ:FTNT", "NASDAQ:AEP", "NASDAQ:ROST",
            "NASDAQ:PLTR", "NASDAQ:COIN", "NASDAQ:MDB", "NASDAQ:ARM", "NASDAQ:QQQ",
            "NASDAQ:SMCI", "NASDAQ:ZS", "NASDAQ:MSTR", "NASDAQ:DDOG"
        ] # 64 assets
        
        self.target_crypto_count = 40
        self.target_bist_count = 20
        self.target_nasdaq_count = 60

        self._force_rotation()

    def _force_rotation(self):
        """Tüm grupları ML/Volatilite (simüle) tabanlı olarak yeniden oluşturur"""
        self.last_rotation_time = time.time()
        
        # Basitçe shuffle yapıp ilk N tanesini alarak "dinamik ML seçimi" mantığını işletiyoruz.
        # Gerçek üretimde buralar hacim ve volatilite apilerinden süzülür.
        shuffled_crypto = list(self.master_crypto_universe)
        random.shuffle(shuffled_crypto)
        self.active_crypto_targets = shuffled_crypto[:self.target_crypto_count]
        
        shuffled_bist = list(self.master_bist_universe)
        random.shuffle(shuffled_bist)
        self.active_bist_targets = sorted(shuffled_bist[:self.target_bist_count])
        
        shuffled_nasdaq = list(self.master_nasdaq_universe)
        random.shuffle(shuffled_nasdaq)
        self.active_nasdaq_targets = sorted(shuffled_nasdaq[:self.target_nasdaq_count])

        # Benchmark'ların (RS Line için) her zaman izlendiğinden emin ol
        if "BINANCE:BTCUSDT" not in self.active_crypto_targets:
            self.active_crypto_targets.append("BINANCE:BTCUSDT")
        if "BIST:XU100" not in self.active_bist_targets:
            self.active_bist_targets.append("BIST:XU100")
        if "NASDAQ:QQQ" not in self.active_nasdaq_targets:
            self.active_nasdaq_targets.append("NASDAQ:QQQ")

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
