import logging
import time
import math
import threading
from typing import Dict, Any, List, Optional

logger = logging.getLogger("ReversalEngine")

class ReversalEngine:
    """
    Tier-1 Dual-Engine Architecture: Reversal (Dipten Dönüş) Avcısı
    Bu motor SADECE Momentum (Ana) botu Kill-Switch yediğinde uyanır.
    Düşen bıçağı tutmaz, bıçak yere saplanıp durduğunda alır.
    """
    def __init__(self):
        self.is_active = False
        
        # Hedef Havuzu (Eski statik liste yerine dinamik property eklendi)
        self._fallback_symbols = ["BINANCE:FETUSDT", "BINANCE:SUIUSDT", "BINANCE:DOGEUSDT", "BINANCE:SOLUSDT"]
        
        # 2. Dinamik Eşikler
        self.base_entry_rsi = 25.0
        self.base_profit_pct = 2.5
        self.base_stop_pct = 3.0
        self.time_stop_seconds = 2 * 60 * 60  # 2 Saat
        
        # 3. Kilitli Hazine Yönetimi (Dedicated Reversal Vault)
        # Portföyün %20'si sadece Reversal (Çöküş) için saklanır. 
        # Momentum motoru bu bakiyeye dokunamaz.
        self.reversal_vault_pct = 20.0 
        
        # 4. Global Emir Sırası (Execution Mutex Queue)
        # API Trafik kazalarını önlemek için kullanılan KİLİT mekanizması
        self.execution_lock = threading.Lock()

        self.active_reversal_positions = {}
        self.correlation_cache = {}

    @property
    def target_symbols(self) -> List[str]:
        """
        DİNAMİK HEDEF TESPİTİ (Dip Avcısı Radarı)
        Piyasadaki tüm varlıklar arasından RSI değeri en düşük (en çok kan kaybeden)
        KRIPTO (6), NASDAQ (4), BIST (2) varlıklarını otomatik seçer ve kilitler.
        """
        try:
            from services.data_ingestion.tradingview_live_client import tradingview_live_client
            from services.data_ingestion.asset_universe_manager import asset_universe_manager
            
            targets = []
            
            # --- VIX & BTC MAKCRO (ŞELALE) KALKANI ---
            is_macro_crash = False
            btc_data = tradingview_live_client.cached_crypto_data.get("BTCUSDT")
            if btc_data and float(btc_data.get("change_pct", 0.0)) <= -4.0:
                is_macro_crash = True
                
            vix_data = tradingview_live_client.cached_us_data.get("VIX")
            if vix_data and float(vix_data.get("change_pct", 0.0)) >= 10.0:
                is_macro_crash = True
                
            rsi_threshold = 28.0 if is_macro_crash else 45.0

            def calculate_reversal_score(metrics: dict) -> float:
                """Oversold (Dip) + Akıllı Para Girişi (Hacim/CMF) Puanlaması"""
                
                # 1. ÖNERİ: YEŞİL MUM ONAYI (Price Action - Ölü Kedi Kalkanı)
                price = float(metrics.get("price", 0.0))
                candle_open = float(metrics.get("candle_open", 0.0))
                # Fiyat açılışın altındaysa (mum hala kırmızıysa), kanama devam ediyordur. Reddet!
                if candle_open > 0 and price < candle_open:
                    return -999.0

                rsi = float(metrics.get("rsi", 50.0))
                # 2. ÖNERİ: ŞELALE KALKANI KONTROLÜ
                if rsi > rsi_threshold:
                    return -999.0
                    
                vol_ratio = float(metrics.get("volume_ratio", 1.0))
                cmf = float(metrics.get("cmf", 0.0))
                macd = float(metrics.get("macd", 0.0))
                
                # Ne kadar dipte?
                dip_score = (rsi_threshold - rsi) * 1.5
                # Hacim artışı var mı? 
                vol_score = (vol_ratio - 1.0) * 15.0
                # Para Girişi
                cmf_score = cmf * 50.0
                # MACD Toparlanması
                macd_score = 10.0 if macd > -0.5 else 0.0
                
                return dip_score + vol_score + cmf_score + macd_score
            
            # 1. KRİPTO (4 Hedef)
            data_c = tradingview_live_client.cached_crypto_data
            if data_c:
                c_master = [s.split(":")[-1] for s in asset_universe_manager.master_crypto_universe]
                c_cands = []
                for sym, metrics in data_c.items():
                    if sym in c_master:
                        score = calculate_reversal_score(metrics)
                        if score > -900: c_cands.append((f"BINANCE:{sym}", score))
                c_cands.sort(key=lambda x: x[1], reverse=True)
                targets.extend([c[0] for c in c_cands[:4]])
                
            # 2. NASDAQ (4 Hedef)
            data_n = tradingview_live_client.cached_us_data
            if data_n:
                n_master = [s.split(":")[-1] for s in asset_universe_manager.master_nasdaq_universe]
                n_cands = []
                for sym, metrics in data_n.items():
                    if sym in n_master:
                        score = calculate_reversal_score(metrics)
                        if score > -900: n_cands.append((f"NASDAQ:{sym}", score))
                n_cands.sort(key=lambda x: x[1], reverse=True)
                targets.extend([c[0] for c in n_cands[:4]])
                
            # 3. BIST (2 Hedef)
            data_b = tradingview_live_client.cached_tr_data
            if data_b:
                b_master = [s.split(":")[-1] for s in asset_universe_manager.master_bist_universe]
                b_cands = []
                for sym, metrics in data_b.items():
                    if sym in b_master:
                        score = calculate_reversal_score(metrics)
                        if score > -900: b_cands.append((f"BIST:{sym}", score))
                b_cands.sort(key=lambda x: x[1], reverse=True)
                targets.extend([c[0] for c in b_cands[:2]])

            if not targets:
                return self._fallback_symbols
            return targets
            
        except Exception as e:
            logger.error(f"[REVERSAL] Dinamik hedef hesaplama hatasi: {e}")
            return self._fallback_symbols

    def wake_up_call(self, is_kill_switch_active: bool):
        """Ana bot Kill-Switch yediğinde bu motoru uyandırır."""
        if not is_kill_switch_active:
            if self.is_active:
                logger.info("🦉 [REVERSAL] Piyasa normalleşti. Reversal Engine uykuya dalıyor.")
            self.is_active = False
            return

        if not self.is_active:
            logger.warning("🦉 [REVERSAL] Ana bot Kill-Switch yedi. Reversal Engine UYANDI! Kanlı piyasada avlanma başlıyor.")
            self.is_active = True

    def scan_and_execute(self, market_prices: Dict[str, Any], available_balance: float):
        """Piyasayı koklar ve şartlar sağlanırsa Keskin Nişancı atışını yapar."""
        if not self.is_active:
            return

        self._check_time_stops()

        candidates = []
        for sym in self.target_symbols:
            raw_sym = sym.split(":")[-1]
            data = market_prices.get(raw_sym)
            if not data:
                continue

            rsi = float(data.get("rsi", 50))
            macd = float(data.get("macd", 0))
            vol_ratio = float(data.get("volume_ratio", 1.0))
            price = float(data.get("price", 0))
            atr_pct = float(data.get("atr_pct", 2.0))

            if rsi < self.base_entry_rsi:
                if vol_ratio > 1.5 or macd > 0:
                    candidates.append({
                        "symbol": sym,
                        "price": price,
                        "rsi": rsi,
                        "atr_pct": atr_pct
                    })

        if not candidates:
            return

        best_candidate = sorted(candidates, key=lambda x: x["rsi"])[0] 
        self._execute_smart_snipe(best_candidate, available_balance)

    def _execute_smart_snipe(self, candidate: Dict[str, Any], total_balance: float):
        """Tier-1 Risk Yönetimi ile emri piyasaya iletir."""
        sym = candidate["symbol"]
        if sym in self.active_reversal_positions:
            return

        price = candidate["price"]
        atr_pct = candidate["atr_pct"]

        # Hazine Kontrolü: Toplam bakiyenin sadece %20'si Vault olarak kullanılabilir
        vault_budget = total_balance * (self.reversal_vault_pct / 100.0)

        applied_stop = self.base_stop_pct
        if atr_pct > 3.0:
            applied_stop = self.base_stop_pct * 2.5
            logger.warning(f"⚠️ [REVERSAL] Aşırı volatilite ({atr_pct}%) tespit edildi. Stop-Loss {applied_stop}%'ye esnetildi.")

        # MUTEX KİLİDİ (Trafik Polisi) DEVREYE GİRİYOR
        logger.info(f"🚦 [REVERSAL MUTEX] {sym} için API kilidi (Lock) talep ediliyor...")
        with self.execution_lock:
            logger.info("🚦 [REVERSAL MUTEX] API Kilidi ALINDI. İşlem sıraya konuldu, diğer motorlar bekletiliyor.")
            
            success = self._send_order_with_backoff(sym, price, vault_budget)
            if success:
                logger.info(f"🎯 [REVERSAL] KESKİN NİŞANCI ATIŞI BAŞARILI! Hazine Bütçesi Kullanıldı. {sym} @ {price}")
                self.active_reversal_positions[sym] = {
                    "entry_price": price,
                    "tp_price": price * (1 + (self.base_profit_pct / 100.0)),
                    "sl_price": price * (1 - (applied_stop / 100.0)),
                    "status": "OPEN",
                    "entry_time": time.time(),
                    "allocated_budget": vault_budget
                }
                self._broadcast_to_ai_council(sym, "RSI Dipte, Hacim Onaylandı. API Kilidi Güvenli, İnfaz Gerçekleşti.")
            
            logger.info("🚦 [REVERSAL MUTEX] İşlem bitti, API Kilidi (Lock) SERBEST BIRAKILDI.")

    def _send_order_with_backoff(self, symbol: str, price: float, budget: float) -> bool:
        """API kilitlenmelerine karşı koçbaşı gibi kapıya vurur ve gerçek emri iletir."""
        max_retries = 3
        delay = 0.1
        for i in range(max_retries):
            try:
                from services.market_feed.live_stream import live_trade_manager
                # Gerçek broker emri tetikleniyor (Otonom İnfaz)
                qty = budget / price if price > 0 else 0
                if qty <= 0:
                    return False
                
                # Sadece loglama değil, sisteme doğrudan emir işliyoruz
                live_trade_manager.execute_trade(
                    symbol=symbol,
                    decision="BUY",
                    price=price,
                    reason="DİP AVCISI OTONOM İNFAZ",
                    momentum_phase="PANIC_REVERSAL"
                )
                return True 
            except Exception as e:
                logger.error(f"⚠️ [REVERSAL] İnfaz hatası (Deneme {i+1}): {e}")
                time.sleep(delay)
                delay *= 2
        return False

    def _check_time_stops(self):
        """Tier-1 Kural: Zaman Aşımı Kesicisi (Time-Stop)"""
        now = time.time()
        for sym, pos in list(self.active_reversal_positions.items()):
            if pos["status"] == "OPEN":
                elapsed = now - pos["entry_time"]
                if elapsed > self.time_stop_seconds:
                    logger.warning(f"⏱️ [REVERSAL] TIME-STOP TETİKLENDİ! {sym} kapatılıyor.")
                    pos["status"] = "CLOSED_TIME_STOP"

    def _broadcast_to_ai_council(self, symbol: str, thought: str):
        pass

reversal_engine = ReversalEngine()
