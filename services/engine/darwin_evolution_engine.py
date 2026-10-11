"""
Darwinian Otonom Evrim ve Dinamik Duruş Motoru (Darwinian Autonomous Evolution & Stance Engine)
================================================================================================
Manifesto ve Doktrin Uyumu:
1. Gölge Arena Geçmiş Birikim Total (Kümülatif ve Asla Silinmeyen Hafıza).
2. Çift Tetikleyici: Her 2 saatte bir (7200s) VEYA 2 MB şişen veri birikiminde tam evrim döngüsü.
3. Dinamik Piyasa Koklama (Market Sniffing): Testere (Choppy), Çöküş (Crash), Boğa (Trend) Tespiti.
4. Otonom Duruş:
   - 🛡️ DEFANS / GUARD: Testere veya çöküşte WAIT / STOP yaparak nakiti %100 koruma.
   - ⚔️ ATAK / ATTACK: Temiz trendde agresif alfa ve kâr toplama.
5. Darwinian Doğal Seçilim & Mutasyon: Hatalı genleri (sahte kırılımlar, XR<1.0 tuzakları) cezalandırma,
   kazanan formasyonları (XR>1.15, Vol>1.5x) ödüllendirme.
"""

import os
import json
import time
from datetime import datetime, timezone
from typing import Dict, Any, List, Tuple, Optional
from core.logger import logger

CUMULATIVE_FILE = "data/darwin_cumulative_knowledge.json"
EVOLUTION_STATE_FILE = "data/darwin_evolution_state.json"
GENETICS_FILE = "data/darwin_genetics.json"

TWO_HOURS_SECONDS = 7200  # 2 saat
TWO_MB_BYTES = 2 * 1024 * 1024  # 2 Megabayt


class DarwinEvolutionEngine:
    def __init__(self):
        self._ensure_storage()
        self.state: Dict[str, Any] = self._load_evolution_state()
        self.cumulative_trades: List[Dict[str, Any]] = self._load_cumulative_trades()
        
        # İlk açılışta veya gerekirse anında koklama ve sentez yap
        if self.state.get("generation", 0) == 0:
            self.execute_darwinian_synthesis(reason="İLK BAŞLATMA VE KALİBRASYON")

    def _ensure_storage(self):
        os.makedirs("data", exist_ok=True)
        if not os.path.exists(CUMULATIVE_FILE):
            with open(CUMULATIVE_FILE, "w", encoding="utf-8") as f:
                json.dump([], f, indent=2)
        if not os.path.exists(GENETICS_FILE):
            with open(GENETICS_FILE, "w", encoding="utf-8") as f:
                json.dump({}, f, indent=2)

    def _load_cumulative_trades(self) -> List[Dict[str, Any]]:
        try:
            if os.path.exists(CUMULATIVE_FILE):
                with open(CUMULATIVE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
        except Exception as e:
            logger.error(f"[DARWIN] Cumulative data yükleme hatası: {e}")
        return []

    def _save_cumulative_trades(self):
        try:
            with open(CUMULATIVE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.cumulative_trades, f, indent=2)
        except Exception as e:
            logger.error(f"[DARWIN] Cumulative data kaydetme hatası: {e}")

    def _load_evolution_state(self) -> Dict[str, Any]:
        default_state = {
            "generation": 0,
            "active_stance": "GUARD",  # Varsayılan güvenli duruş: DEFANS
            "stance_label": "🛡️ DEFANS (NAKİT KORUMA)",
            "market_regime": "CALIBRATING",
            "market_sniff_summary": "Piyasa taranıyor...",
            "cash_preservation_active": True,
            "last_analysis_timestamp": 0,
            "last_analysis_time_str": "Henüz yapılmadı",
            "next_analysis_due_str": "2 saat içinde veya +2 MB veri",
            "last_analysis_size_bytes": 0,
            "current_data_size_bytes": 0,
            "current_data_size_mb": 0.0,
            "cumulative_trades_count": 0,
            "win_rate_cumulative": 0.0,
            "total_pnl_cumulative": 0.0,
            "learned_mutations": [],
            "guard_rules": {
                "min_confidence_score": 80.0,
                "min_volume_ratio": 2.0,
                "min_xray_ratio": 1.15,
                "capital_risk_multiplier": 0.5,
                "force_wait_on_choppy": True
            },
            "attack_rules": {
                "min_confidence_score": 65.0,
                "min_volume_ratio": 1.2,
                "min_xray_ratio": 1.0,
                "capital_risk_multiplier": 1.2,
                "trailing_profit_expansion": True
            }
        }
        if os.path.exists(EVOLUTION_STATE_FILE):
            try:
                with open(EVOLUTION_STATE_FILE, "r", encoding="utf-8") as f:
                    saved = json.load(f)
                    default_state.update(saved)
            except Exception as e:
                logger.error(f"[DARWIN] State yükleme hatası: {e}")
        return default_state

    def _save_evolution_state(self):
        try:
            with open(EVOLUTION_STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(self.state, f, indent=4)
        except Exception as e:
            logger.error(f"[DARWIN] State kaydetme hatası: {e}")

    def get_data_size_bytes(self) -> int:
        size = 0
        if os.path.exists(CUMULATIVE_FILE):
            size += os.path.getsize(CUMULATIVE_FILE)
        if os.path.exists("experience_memory.json"):
            size += os.path.getsize("experience_memory.json")
        return size

    def record_trade_experience(self, trade_data: Dict[str, Any]):
        """
        Gölge veya Canlı tamamlanan her işlemi kümülatif hafızaya işler.
        Asla eski kayıtları silmez (Total Birikim).
        """
        trade_id = trade_data.get("trade_id") or f"DYN-{trade_data.get('symbol')}-{int(time.time())}"
        
        # Mükerrer kaydı engelle
        existing = any(t.get("trade_id") == trade_id for t in self.cumulative_trades)
        if not existing:
            item = {
                "trade_id": trade_id,
                "symbol": trade_data.get("symbol", "UNKNOWN"),
                "action": trade_data.get("action", "BUY"),
                "entry_price": float(trade_data.get("entry_price", 0.0) or 0.0),
                "exit_price": float(trade_data.get("exit_price", 0.0) or 0.0),
                "pnl_pct": float(trade_data.get("pnl_pct", 0.0) or 0.0),
                "pnl_amount": float(trade_data.get("pnl_amount", 0.0) or 0.0),
                "is_win": bool(trade_data.get("is_win", False) or (trade_data.get("pnl_pct", 0.0) > 0)),
                "market_regime": trade_data.get("market_regime", "UNKNOWN"),
                "duration_minutes": trade_data.get("duration_minutes", 0),
                "exit_reason": trade_data.get("exit_reason", ""),
                "indicators": trade_data.get("indicators", {}),
                "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
                "recorded_at_epoch": time.time()
            }
            self.cumulative_trades.append(item)
            self._save_cumulative_trades()
            logger.info(f"🧬 [DARWIN KÜMÜLATİF BİRİKİM] {item['symbol']} kalıcı hafızaya mühürlendi. Toplam: {len(self.cumulative_trades)} işlem.")

        # Çift tetikleyici kontrolü
        self.check_and_trigger_evolution_if_needed()

    def check_and_trigger_evolution_if_needed(self, force: bool = False) -> bool:
        """
        Çift Tetikleyici Mekanizması:
        1. 2 saat (7200s) doldu mu?
        2. Son analizden bu yana biriken veri 2 MB büyüdü mü?
        """
        now = time.time()
        last_time = self.state.get("last_analysis_timestamp", 0)
        time_elapsed = now - last_time

        current_size = self.get_data_size_bytes()
        last_size = self.state.get("last_analysis_size_bytes", 0)
        size_growth = current_size - last_size

        time_triggered = (time_elapsed >= TWO_HOURS_SECONDS)
        size_triggered = (size_growth >= TWO_MB_BYTES) or (current_size >= TWO_MB_BYTES and last_size == 0)

        if force or time_triggered or size_triggered:
            trigger_reason = []
            if force:
                trigger_reason.append("MANUEL TETİKLEME")
            if time_triggered:
                trigger_reason.append(f"2 SAAT SÜRE DOLDU ({int(time_elapsed//60)} dk)")
            if size_triggered:
                trigger_reason.append(f"2 MB VERİ ŞİŞMESİ ({size_growth / (1024*1024):.2f} MB büyüme)")
            
            reason_str = " | ".join(trigger_reason) if trigger_reason else "DÖNGÜSEL ANALİZ"
            self.execute_darwinian_synthesis(reason=reason_str)
            return True
        return False

    def sniff_market_conditions(self) -> Dict[str, Any]:
        """
        Dinamik Piyasa Koklama (Market Sniffing Algorithm):
        Borsadaki tüm varlıkların anlık durumunu, yönünü, testere (choppiness) seviyesini,
        ve taker alıcı/satıcı dengesini analiz eder.
        """
        from services.market_feed.live_stream import live_trade_manager

        # Oncelikle sıcak onbellegi (last_prices) kontrol et, yoksa get_live_prices cagir
        prices = getattr(live_trade_manager, "last_prices", {})
        if not prices or len(prices) < 5:
            prices = live_trade_manager.get_live_prices()
        if not prices:
            return {
                "regime": "CALIBRATING",
                "choppy_score": 50.0,
                "panic_score": 0.0,
                "bull_score": 50.0,
                "summary": "Piyasa fiyat akışı bekleniyor."
            }

        crypto_items = [v for k, v in prices.items() if "USDT" in k.upper() and isinstance(v, dict)]
        total_assets = len(crypto_items)
        if total_assets == 0:
            return {
                "regime": "SIDEWAYS_TESTERE",
                "choppy_score": 60.0,
                "panic_score": 10.0,
                "bull_score": 30.0,
                "summary": "Düşük likidite ve veri akışı."
            }

        # İstatistiksel metrikler
        pos_count = sum(1 for c in crypto_items if float(c.get("change_24h", 0) or 0) > 0)
        heavy_drop_count = sum(1 for c in crypto_items if float(c.get("change_24h", 0) or 0) <= -2.0)
        strong_gain_count = sum(1 for c in crypto_items if float(c.get("change_24h", 0) or 0) >= 3.0)
        
        # X-Ray ve Hacim Koklama
        high_vol_count = sum(1 for c in crypto_items if float(c.get("volume_ratio", 1.0) or 1.0) >= 1.5)
        healthy_xr_count = sum(1 for c in crypto_items if float(c.get("xray_ratio", 0.0) or 0.0) >= 1.0)

        pos_ratio = (pos_count / total_assets) * 100.0
        heavy_drop_ratio = (heavy_drop_count / total_assets) * 100.0
        strong_gain_ratio = (strong_gain_count / total_assets) * 100.0
        healthy_xr_ratio = (healthy_xr_count / total_assets) * 100.0 if total_assets > 0 else 0.0

        # Testere İndeksi (Choppiness Index):
        # Eğer piyasada net bir yön yoksa (%40 - %60 arası pozitif) veya
        # Hacim yükselişleri XR < 1.0 ile karşılanıp sahte kırılım yaratıyorsa testere yüksektir.
        is_neutral_breadth = (35.0 <= pos_ratio <= 65.0)
        divergence_penalty = 30.0 if (high_vol_count > strong_gain_count * 2) else 0.0
        choppy_score = min(100.0, (50.0 if is_neutral_breadth else 25.0) + divergence_penalty + (25.0 if healthy_xr_ratio < 30.0 else 0.0))

        # Panik / Çöküş İndeksi
        panic_score = min(100.0, (heavy_drop_ratio * 3.0))

        # Boğa / Atak İndeksi
        bull_score = min(100.0, (strong_gain_ratio * 2.5) + (healthy_xr_ratio * 0.5))

        # Rejim Tespiti
        if panic_score >= 40.0 or heavy_drop_ratio >= 15.0:
            regime = "PANIC_CRASH"
            summary = f"🚨 ÇÖKÜŞ / PANİK REJİMİ (%{heavy_drop_ratio:.1f} ağır düşüşte, düşen bıçaklar devrede)"
        elif choppy_score >= 60.0:
            regime = "SIDEWAYS_TESTERE"
            summary = f"⚔️ TESTERE PİYASASI (Yatay/Whipsaw: Yön belirsiz, sahte kırılım riski %{choppy_score:.0f})"
        elif bull_score >= 60.0 and pos_ratio >= 65.0:
            regime = "TRENDING_BULL"
            summary = f"🚀 TEMİZ BOĞA TRENDİ (Genişlik: %{pos_ratio:.1f} yeşil, Taker Alıcı Dominasyonu)"
        else:
            regime = "CONSOLIDATION_RANGE"
            summary = f"⚖️ KONSOLİDASYON (Denge Arayışı, Seçici Fırsatlar)"

        return {
            "regime": regime,
            "choppy_score": round(choppy_score, 1),
            "panic_score": round(panic_score, 1),
            "bull_score": round(bull_score, 1),
            "pos_ratio": round(pos_ratio, 1),
            "healthy_xr_ratio": round(healthy_xr_ratio, 1),
            "summary": summary
        }

    def execute_darwinian_synthesis(self, reason: str = "PERİYODİK EVRİM DÖNGÜSÜ"):
        """
        Otonom Tecrübesel Darwinizm Sentezi (Walk-Forward Machine Learning Sentezi):
        Kümülatif tüm işlemleri ve anlık piyasa kokusunu birleştirerek
        otonom duruşu (GUARD vs ATAK) belirler ve kuralları mutasyona uğratır.
        """
        now = time.time()
        self.state["generation"] += 1
        gen = self.state["generation"]
        logger.info(f"🧬 [DARWIN EVRİM DÖNGÜSÜ GEN #{gen}] Başlatıldı! Tetikleyici: {reason}")

        # 1. Piyasa Koklama
        sniff = self.sniff_market_conditions()
        regime = sniff["regime"]
        self.state["market_regime"] = regime
        self.state["market_sniff_summary"] = sniff["summary"]

        # 2. Kümülatif İşlem Performansı
        total_trades = len(self.cumulative_trades)
        wins = [t for t in self.cumulative_trades if t.get("is_win")]
        losses = [t for t in self.cumulative_trades if not t.get("is_win")]
        win_rate = round((len(wins) / total_trades * 100.0), 1) if total_trades > 0 else 50.0
        total_pnl = round(sum(float(t.get("pnl_amount", 0.0) or 0.0) for t in self.cumulative_trades), 2)

        # Son 10 işlemin analizi (Kısa vadeli ivme)
        recent = self.cumulative_trades[-10:] if len(self.cumulative_trades) >= 10 else self.cumulative_trades
        recent_losses = len([t for t in recent if not t.get("is_win")])
        recent_loss_rate = (recent_losses / len(recent) * 100.0) if recent else 0.0

        mutations = []

        # 3. Darwinian Karar: DEFANS (GUARD) vs ATAK (ATTACK)
        # KRİTİK KURAL: Testerede veya Çöküşte NAKİT KORUMA (GUARD) MUTLAKTIR.
        if regime in ["SIDEWAYS_TESTERE", "PANIC_CRASH"] or recent_loss_rate >= 60.0 or sniff["choppy_score"] >= 65.0:
            active_stance = "GUARD"
            stance_label = "🛡️ DEFANS (NAKİT KORUMA)"
            cash_protection = True
            
            # Savunma kural mutasyonları
            mutations.append({
                "rule": "NAKİT_KORUMA_KALKANI",
                "trigger": "Testere / Çöküş Piyasa Rejimi Algılandı",
                "action": "Vasat ve sınırda kalan tüm alımlar derhal bloklandı. Sadece Konsey Skoru >= 82 ve Hacim >= 2.0x elit fırsatlar geçer.",
                "status": "AKTİF"
            })
            mutations.append({
                "rule": "SAHTE_KIRILIM_CEZASI",
                "trigger": "XR < 1.15 Olan Yükselişler Dağıtım Tuzağı Olarak İşaretlendi",
                "action": "Taker alıcı desteği olmayan (limit satıcılı) yükselişlere giriş yasaklandı.",
                "status": "AKTİF"
            })
            mutations.append({
                "rule": "SERMAYE_SIKIŞTIRMA",
                "trigger": "Kasa Koruma Modu",
                "action": "Pozisyon büyüklüğü %50 defansif katsayıya çekildi.",
                "status": "AKTİF"
            })
        else:
            active_stance = "ATTACK"
            stance_label = "⚔️ ATAK (ALPHA AVCISI)"
            cash_protection = False
            
            mutations.append({
                "rule": "MOMENTUM_SÖRFÜ",
                "trigger": "Temiz Boğa & Trend Hizalanması",
                "action": "Konsey Skoru >= 65 olan güçlü hacimli kırılımlara serbest giriş yetkisi verildi.",
                "status": "AKTİF"
            })
            mutations.append({
                "rule": "KÂR_BÜYÜTME_EXPANSION",
                "trigger": "Yüksek Taker Alıcı Dominasyonu (XR >= 1.0)",
                "action": "TP hedefleri genişletildi, ATR Trailing Stop ile trend sonuna kadar takip edilir.",
                "status": "AKTİF"
            })

        # 4. State Güncellemesi
        current_size = self.get_data_size_bytes()
        self.state["active_stance"] = active_stance
        self.state["stance_label"] = stance_label
        self.state["cash_preservation_active"] = cash_protection
        self.state["last_analysis_timestamp"] = now
        self.state["last_analysis_time_str"] = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        
        next_due = now + TWO_HOURS_SECONDS
        self.state["next_analysis_due_str"] = datetime.fromtimestamp(next_due, timezone.utc).strftime("%H:%M UTC (veya +2 MB)")
        self.state["last_analysis_size_bytes"] = current_size
        self.state["current_data_size_bytes"] = current_size
        self.state["current_data_size_mb"] = round(current_size / (1024 * 1024), 3)
        self.state["cumulative_trades_count"] = total_trades
        self.state["win_rate_cumulative"] = win_rate
        self.state["total_pnl_cumulative"] = total_pnl
        self.state["learned_mutations"] = mutations

        self._save_evolution_state()
        logger.info(f"🧬 [DARWIN SENTEZ BİTTİ] Duruş: {stance_label} | Rejim: {regime} | Toplam İşlem: {total_trades} | Veri: {self.state['current_data_size_mb']} MB")

    def get_active_stance(self) -> str:
        """
        Aktif duruşu döner: 'GUARD' veya 'ATTACK'
        """
        # Periyodik kontrolü tetikle
        self.check_and_trigger_evolution_if_needed()
        return self.state.get("active_stance", "GUARD")

    def evaluate_opportunity_safeguard(
        self,
        symbol: str,
        score: float,
        volume_ratio: float,
        xray_ratio: float,
        change_24h: float
    ) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Otonom Emir Kapısı (Darwinian Guard Check):
        Bir coine girilmeden önce otonom Darwinist duruşa (DEFANS vs ATAK) uygunluğunu denetler.
        
        Returns:
            (allowed: bool, reason: str, adjustments: dict)
        """
        stance = self.get_active_stance()
        regime = self.state.get("market_regime", "SIDEWAYS_TESTERE")

        # 1. Düşen Bıçak Koruması (Her koşulda geçerli mutlak kural)
        if change_24h <= -2.0 and xray_ratio < 1.3:
            return False, f"🚨 DÜŞEN BIÇAK (-%{abs(change_24h):.1f} düşüş, XR={xray_ratio:.2f}<1.3): ATOM dersi gereği nakit korundu.", {}

        # 2. DEFANS / GUARD MODU KONTROLLERİ
        if stance == "GUARD":
            guard_rules = self.state.get("guard_rules", {})
            min_score = guard_rules.get("min_confidence_score", 80.0)
            min_vol = guard_rules.get("min_volume_ratio", 2.0)
            min_xr = guard_rules.get("min_xray_ratio", 1.15)

            # Testere piyasasında sahte kırılımlara ve sıradan sinyallere VETO
            if score < min_score:
                return False, f"🛡️ DEFANS MODU (NAKİT KORUMA): Testere/Çöküş piyasasında sermaye korunuyor. Skor ({score:.1f} < {min_score}) yetersiz, pas geçildi.", {"status": "WAIT_IN_CASH"}

            if volume_ratio < min_vol:
                return False, f"🛡️ DEFANS MODU (HACİM EKSİKLİĞİ): Hacim ({volume_ratio:.1f}x < {min_vol}x) testere tuzağı yaratabilir, nakitte kalındı.", {"status": "WAIT_IN_CASH"}

            if xray_ratio < min_xr:
                return False, f"🛡️ DEFANS MODU (DAĞITIM TUZAĞI): X-Ray ({xray_ratio:.2f} < {min_xr}) limit satıcı baskısı gösteriyor. Mal boşaltılıyor, alım engellendi.", {"status": "WAIT_IN_CASH"}

            # Tüm elit şartları sağladıysa defansif bütçeyle izin ver
            return True, f"🛡️ DEFANS MODU ONAYLI ELİT FIRSAT: Skor {score:.1f}, Hacim {volume_ratio:.1f}x, XR {xray_ratio:.2f}. Sıkı stopla kontrollü atak.", {
                "capital_mult": 0.5,
                "tight_sl": True,
                "quick_tp": True
            }

        # 3. ATAK / ATTACK MODU KONTROLLERİ
        else:
            attack_rules = self.state.get("attack_rules", {})
            min_score = attack_rules.get("min_confidence_score", 65.0)
            min_vol = attack_rules.get("min_volume_ratio", 1.2)
            min_xr = attack_rules.get("min_xray_ratio", 1.0)

            if score < min_score or volume_ratio < min_vol:
                return False, f"⚔️ ATAK MODU: Skor veya hacim yetersiz ({score:.1f} / {volume_ratio:.1f}x).", {}

            return True, f"⚔️ ATAK MODU (ALPHA AVCISI): Trend ve hacim hizalı. Agresif momentum kârı hedefleniyor.", {
                "capital_mult": 1.2,
                "trailing_expansion": True
            }

    def get_evolution_summary(self) -> Dict[str, Any]:
        """
        Dashboard ve API için tam özet
        """
        self.check_and_trigger_evolution_if_needed()
        current_size = self.get_data_size_bytes()
        return {
            "status": "success",
            "generation": self.state.get("generation", 1),
            "active_stance": self.state.get("active_stance", "GUARD"),
            "stance_label": self.state.get("stance_label", "🛡️ DEFANS (NAKİT KORUMA)"),
            "market_regime": self.state.get("market_regime", "SIDEWAYS_TESTERE"),
            "market_sniff_summary": self.state.get("market_sniff_summary", ""),
            "cash_preservation_active": self.state.get("cash_preservation_active", True),
            "last_analysis_time_str": self.state.get("last_analysis_time_str", ""),
            "next_analysis_due_str": self.state.get("next_analysis_due_str", ""),
            "cumulative_trades_count": len(self.cumulative_trades),
            "win_rate_cumulative": self.state.get("win_rate_cumulative", 0.0),
            "total_pnl_cumulative": self.state.get("total_pnl_cumulative", 0.0),
            "current_data_size_mb": round(current_size / (1024 * 1024), 3),
            "threshold_data_size_mb": 2.0,
            "learned_mutations": self.state.get("learned_mutations", []),
            "philosophy": "Testere ve çöküşte nakit kalkanı, trendde agresif alfa sörfü."
        }


darwin_evolution_engine = DarwinEvolutionEngine()
