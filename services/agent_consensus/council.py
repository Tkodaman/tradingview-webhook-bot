import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

class OBIAgent:
    """Emir Defteri Dengesizliği (Orderbook Imbalance) Ajanı"""
    def evaluate(self, signal: Any, current_price: float) -> Dict[str, Any]:
        indicators = getattr(signal, 'indicators', {}) or {}
        spread_pct = indicators.get("spread_pct", 0.1)
        obi = float(indicators.get("obi", 0.0)) 
        
        if obi < -0.5:
            return {"approved": True, "reason": f"RİSK: OBI (-{abs(obi):.2f}) Satıcı Duvarı! (Spread: %{spread_pct})", "score": 20}
        if spread_pct > 0.8:
            return {"approved": True, "reason": f"RİSK: Makas korkunç seviyede (%{spread_pct}).", "score": 10}
        if obi > 0.3:
            return {"approved": True, "reason": f"OBI ({obi:.2f}) Güçlü Alıcı Baskısı.", "score": 100}
        return {"approved": True, "reason": f"OBI Nötr ({obi:.2f}).", "score": 75}


class MacroAgent:
    """Makro Rejim ve Hacim Dedektifi"""
    def evaluate(self, signal: Any) -> Dict[str, Any]:
        indicators = getattr(signal, 'indicators', {}) or {}
        vol_ratio = float(indicators.get("volume_ratio", 1.0))
        atr_pct = float(indicators.get("atr_pct", 1.5))
        action = getattr(signal, 'action', '').upper()
        
        if action in ["BUY", "LONG"]:
            if atr_pct < 1.0 and vol_ratio < 1.0:
                return {"approved": True, "score": 30, "reason": f"Düşük İvme (ATR: %{atr_pct}, Vol: {vol_ratio}x)."}
            if vol_ratio >= 1.5:
                return {"approved": True, "score": 100, "reason": f"Mükemmel Momentum! Hacim: {vol_ratio}x"}
        return {"approved": True, "score": 85, "reason": "Makro standartlara uygun."}

class WhaleReactionAgent:
    """Balina Tepki ve Toksik Akış İnfazcısı"""
    def evaluate(self, signal: Any) -> Dict[str, Any]:
        indicators = getattr(signal, 'indicators', {}) or {}
        cmf = float(indicators.get("cmf", 0.0))
        vol_ratio = float(indicators.get("volume_ratio", 1.0))
        
        if cmf < -0.2 and vol_ratio > 2.0:
            return {"approved": True, "score": 25, "reason": f"RİSK: Balinalar MAL BOŞALTIYOR (CMF: {cmf})."}
        elif cmf > 0.2 and vol_ratio > 1.5:
            return {"approved": True, "score": 100, "reason": f"Güçlü Balina Alımı (CMF: {cmf})."}
        return {"approved": True, "score": 75, "reason": "Balina tepkisi nötr."}

class SocialFomoAgent:
    """Anlık Sosyal Medya FOMO ve Haber Akışı Dedektifi (Yürütme Birimi)"""
    def evaluate(self, signal: Any) -> Dict[str, Any]:
        indicators = getattr(signal, 'indicators', {}) or {}
        # Yavaş LLM sorguları (Donukluk) yerine anlık hesaplanmış kantitatif FOMO verisi kullanılır
        fomo_score = int(indicators.get("fomo_score", indicators.get("fear_greed", 50)))
        
        if fomo_score > 80:
            return {"approved": True, "score": 100, "reason": f"AŞIRI FOMO! Sosyal Medya Coşkusu (Skor: {fomo_score}) - Bütçe Esnetilebilir."}
        elif fomo_score < 30:
            return {"approved": False, "score": 10, "reason": f"RİSK: Toksik Akış / Kötü Haber Korkusu (Skor: {fomo_score})"}
        return {"approved": True, "score": fomo_score, "reason": f"Sosyal Duyarlılık Nötr (Skor: {fomo_score})"}

class MarketRegimeAgent:
    """Piyasa Trendi ve Rejim Analisti (Hummingbot Konsepti Entegreli)"""
    def evaluate(self, signal: Any) -> Dict[str, Any]:
        indicators = getattr(signal, 'indicators', {}) or {}
        ema_gc = indicators.get("ema_golden_cross", False)
        adx = float(indicators.get("adx", 20.0))
        
        if ema_gc and adx > 25:
            return {"approved": True, "score": 100, "reason": "Güçlü Boğa Rejimi (Golden Cross + ADX>25). Rüzgar arkamızda!"}
        elif not ema_gc and adx > 25:
            return {"approved": True, "score": 40, "reason": "Dikkat: Ayı Rejimi veya Düzeltme (Death Cross + ADX>25)."}
        else:
            # HUMMINGBOT Entegrasyonu: Testere piyasasında Grid Modu bayrağı kaldır.
            return {"approved": True, "score": 60, "reason": "Yatay / Kararsız Rejim (Ranging). Hummingbot Izgara (Grid) Modu önerilir.", "mode": "GRID"}

class FlashKeyFigureAgent:
    """Sosyal Tetikleyici / Kriz Ajanı (Trump2Cash Konsepti)"""
    def evaluate(self, signal: Any) -> Dict[str, Any]:
        symbol = getattr(signal, 'symbol', 'UNKNOWN')
        try:
            from services.data_ingestion.social_sentiment_tracker import social_tracker
            sentiment_flash = social_tracker.check_for_flash_override(symbol)
        except Exception as e:
            logger.warning(f"[FLASH AGENT] Tracker yüklenemedi: {e}")
            sentiment_flash = getattr(signal, 'flash_sentiment', 'NONE')
            
        if sentiment_flash == 'EXTREME_BULL':
            return {"approved": True, "score": 100, "reason": "FLASH OVERRIDE: Kilit Figürden (Key Figure) Boğa Açıklaması!", "override": True}
        elif sentiment_flash == 'EXTREME_BEAR':
            return {"approved": False, "score": 0, "reason": "FLASH OVERRIDE: Kilit Figürden (Key Figure) Ayı Açıklaması!", "override": True}
        return {"approved": True, "score": 50, "reason": "Flash sosyal tetikleyici yok."}

class LLMChiefJusticeAgent:
    """Yapay Zeka Baş Yargıcı (Debate & RAG Memory)"""
    def evaluate(self, signal: Any) -> Dict[str, Any]:
        symbol = getattr(signal, 'symbol', 'UNKNOWN')
        indicators = getattr(signal, 'indicators', {}) or {}
        try:
            from services.ai.llm_master_agent import llm_master_agent
            if llm_master_agent.is_ready():
                res = llm_master_agent.analyze_signal(symbol, indicators, score=80.0)
                llm_action = res.get("action", "WAIT")
                conf = res.get("confidence", 50)
                bull_case = res.get("bull_case", "")
                bear_case = res.get("bear_case", "")
                
                if llm_action in ["BUY", "LONG"]:
                    return {"approved": True, "score": conf, "reason": f"YZ ONAYI (Boğa Argümanı): {bull_case[:50]}..."}
                elif llm_action == "SELL":
                    return {"approved": True, "score": 100 - conf, "reason": f"YZ VETO (Ayı Argümanı): {bear_case[:50]}..."}
                else:
                    return {"approved": True, "score": 50, "reason": "YZ Kararsız (WAIT). Tartışma nötr sonuçlandı."}
        except Exception as e:
            logger.warning(f"[CHIEF JUSTICE] Hata: {e}")
        return {"approved": True, "score": 50, "reason": "Baş Yargıç çevrimdışı."}


class AutonomousCouncil:
    """Yüce Divan: 7 Ajanlı Kurumsal Kantitatif Zeka Ağı (Grand Council)"""
    def __init__(self):
        self.agents = {
            "OBI": OBIAgent(),
            "MACRO": MacroAgent(),
            "WHALE": WhaleReactionAgent(),
            "NEWS": SocialFomoAgent(),
            "REGIME": MarketRegimeAgent(),
            "FLASH": FlashKeyFigureAgent(),
            "CHIEF_JUSTICE": LLMChiefJusticeAgent()
        }
        
    def convene(self, signal: Any) -> Dict[str, Any]:
        price = getattr(signal, 'price', 0)
        results = {}
        total_score = 0
        
        # Yargı Sonrası ML Düzeltme / Yapılandırma (Dynamic Weight Reconfiguration)
        import os, json
        dynamic_weights_path = os.path.join(os.path.dirname(__file__), '..', 'ai', 'dynamic_weights.json')
        
        weights = {
            "OBI": 0.10,          # %10 Mikro Yapı
            "MACRO": 0.20,        # %20 Hacim
            "WHALE": 0.20,        # %20 Balina Akışı
            "NEWS": 0.10,         # %10 Haber
            "REGIME": 0.15,       # %15 Trend
            "FLASH": 0.0,         # %0 (Override özelliği var)
            "CHIEF_JUSTICE": 0.25 # %25 LLM Tartışma & Hafıza
        }
        
        if os.path.exists(dynamic_weights_path):
            try:
                with open(dynamic_weights_path, 'r') as f:
                    new_weights = json.load(f)
                    for k in weights.keys():
                        if k in new_weights:
                            weights[k] = float(new_weights[k])
            except Exception:
                pass # Hata durumunda varsayılan ağırlıklarla devam et
        
        for name, agent in self.agents.items():
            if name == "OBI":
                res = agent.evaluate(signal, price)
            else:
                res = agent.evaluate(signal)
            results[name] = res
            
            # TRUMP2CASH FLASH OVERRIDE MANTIĞI
            if name == "FLASH" and res.get("override"):
                logger.info(f"🏛️ [YASAMA/YÜRÜTME BYPASS] Olağanüstü Durum! {res['reason']}")
                return {"approved": res["approved"], "reason": res["reason"], "score": res["score"], "mode": "FLASH"}
            
            total_score += res.get("score", 0) * weights[name]
        
        logger.info(f"📜 [YASAMA BİRİMİ] Kurallar ve sınırlar belirlendi. Ajanlar piyasayı taradı.")
        logger.info(f"⚙️ [DERİN ANALİZ & YÜRÜTME] Fonksiyonel ve Kantitatif Veri Toplandı. (Skor: {total_score:.1f})")
        logger.info(f"⚖️ [YARGI BİRİMİ] Baş Yargıç ve Konsey son kararı veriyor...")

        # HUMMINGBOT GRID MODE KONTROLÜ
        if results["REGIME"].get("mode") == "GRID":
            return {"approved": True, "reason": f"YARGI KARARI: YATAY PİYASA (GRID MODU ONAYLANDI) ({total_score:.1f}/100)", "score": total_score, "mode": "GRID"}
        
        # Tam Otonom Cüretkar Mod (Geçer Not: 35'e düşürüldü - Korku Zincirleri Kırıldı!)
        if total_score >= 35:
            reason_str = " | ".join([f"{k}: {v['reason']}" for k,v in results.items() if v.get("score",0) > 60])
            return {"approved": True, "reason": f"YARGI KARARI (ONAY - CÜRETKAR) ({total_score:.1f}/100) - {reason_str}", "score": total_score, "mode": "DIRECTIONAL"}
        else:
            reason_str = " | ".join([f"{k}: {v['reason']}" for k,v in results.items() if v.get("score",100) <= 50])
            return {"approved": False, "reason": f"YARGI KARARI (RED - RİSKLİ) ({total_score:.1f}/100). Sebepler: {reason_str}", "score": total_score, "mode": "NONE"}

council_engine = AutonomousCouncil()
