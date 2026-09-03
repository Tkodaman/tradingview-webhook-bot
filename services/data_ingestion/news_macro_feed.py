import time
import feedparser
from typing import List, Dict, Any
from deep_translator import GoogleTranslator
from core.logger import logger

# Sözlük tabanlı Finansal ve Jeopolitik Duygu & Risk Analiz Ağırlıkları
POSITIVE_KEYWORDS = [
    "agreement", "deal", "growth", "rally", "easing", "rate cut", "bullish", "profit",
    "bilateral trade", "cooperation", "stimulus", "recovery", "expansion", "anlaşma",
    "büyüme", "faiz indirimi", "iş birliği", "teşvik", "yükseliş", "kazanç", "ortaklık"
]

NEGATIVE_KEYWORDS = [
    "sanction", "tariff", "war", "conflict", "rate hike", "inflation", "recession",
    "crackdown", "default", "crisis", "plunge", "ban", "yaptırım", "gümrük vergisi",
    "savaş", "gerilim", "faiz artışı", "enflasyon", "durgunluk", "kriz", "çöküş", "yasak"
]

HIGH_IMPACT_MACRO_KEYWORDS = [
    "fed", "fomc", "ecb", "cbrt", "tcmb", "interest rate", "cpi", "nfp", "gdp", "opec",
    "trade war", "embargo", "faiz kararı", "enflasyon verisi", "ticaret savaşı"
]

# Canlı finans haber kaynakları RSS
DEFAULT_RSS_FEEDS = [
    "https://feeds.finance.yahoo.com/rss/2.0/headline?s=^GSPC,^DJI,BTC-USD",
    "https://www.investing.com/rss/news_25.rss" # Forex / Macro news
]

class NewsMacroFeedService:
    """
    Dünya haberleri, uluslararası ticaret/anlaşmalar, faiz ve makroekonomik duygu analiz servisi.
    """
    def __init__(self):
        self.cached_news: List[Dict[str, Any]] = []
        self.last_fetch_time = 0.0
        self.cache_ttl = 300 # 5 minutes

    def fetch_live_news(self) -> List[Dict[str, Any]]:
        """
        RSS kaynaklarından ve finansal akışlardan haberleri çeker ve etiketler.
        """
        now = time.time()
        if self.cached_news and (now - self.last_fetch_time < self.cache_ttl):
            return self.cached_news

        news_items = []
        for feed_url in DEFAULT_RSS_FEEDS:
            try:
                parsed = feedparser.parse(feed_url)
                for entry in parsed.entries[:10]:
                    title = getattr(entry, "title", "")
                    summary = getattr(entry, "summary", "")
                    published = getattr(entry, "published", "")
                    link = getattr(entry, "link", "")
                    
                    analysis = self.analyze_text_sentiment(f"{title} {summary}")
                    
                    # Çeviri işlemi (İngilizce -> Türkçe)
                    try:
                        tr_title = GoogleTranslator(source='auto', target='tr').translate(title) if title else ""
                        tr_summary = GoogleTranslator(source='auto', target='tr').translate(summary[:200]) if summary else ""
                    except Exception as trans_err:
                        logger.warning(f"Translation error: {trans_err}")
                        tr_title = title
                        tr_summary = summary[:200]

                    news_items.append({
                        "title": tr_title,
                        "summary": tr_summary,
                        "published": published,
                        "link": link,
                        "sentiment_score": analysis["sentiment_score"],
                        "macro_impact_score": analysis["macro_impact_score"],
                        "category": analysis["category"],
                        "keywords_matched": analysis["keywords_matched"]
                    })
            except Exception as e:
                logger.warning(f"Error fetching RSS from {feed_url}: {e}")

        # Eğer RSS çekilemezse varsayılan piyasa/makro veri setini hazır tut
        if not news_items:
            news_items = self._get_fallback_macro_events()

        self.cached_news = news_items
        self.last_fetch_time = now
        return self.cached_news

    def analyze_text_sentiment(self, text: str) -> Dict[str, Any]:
        text_lower = text.lower()
        pos_count = sum(1 for kw in POSITIVE_KEYWORDS if kw in text_lower)
        neg_count = sum(1 for kw in NEGATIVE_KEYWORDS if kw in text_lower)
        impact_count = sum(1 for kw in HIGH_IMPACT_MACRO_KEYWORDS if kw in text_lower)
        
        # -100 (Aşırı Negatif) ile +100 (Aşırı Pozitif)
        if pos_count + neg_count > 0:
            sentiment_score = ((pos_count - neg_count) / (pos_count + neg_count)) * 100.0
        else:
            sentiment_score = 0.0

        # Makro Etki Şiddeti (0 - 100)
        macro_impact = min(100.0, impact_count * 30.0 + (pos_count + neg_count) * 10.0)

        # Kategori tespiti
        category = "GENERAL"
        if any(w in text_lower for w in ["rate", "fed", "faiz", "inflation", "cpi", "tcmb"]):
            category = "CENTRAL_BANK_MONETARY"
        elif any(w in text_lower for w in ["trade", "agreement", "sanction", "tariff", "anlaşma", "yaptırım"]):
            category = "GEOPOLITICAL_TRADE"
        elif any(w in text_lower for w in ["war", "conflict", "savaş", "gerilim"]):
            category = "GLOBAL_CONFLICT"

        return {
            "sentiment_score": round(sentiment_score, 2),
            "macro_impact_score": round(macro_impact, 2),
            "category": category,
            "keywords_matched": [w for w in (POSITIVE_KEYWORDS + NEGATIVE_KEYWORDS + HIGH_IMPACT_MACRO_KEYWORDS) if w in text_lower]
        }

    def evaluate_macro_risk(self, symbol: str, custom_macro_tags: List[str] = None) -> Dict[str, Any]:
        """
        Anlık haberler ve sembol/makro etiketlerini değerlendirerek makro risk katsayısı çıkarır.
        """
        all_news = self.fetch_live_news()
        custom_tags = [t.lower() for t in (custom_macro_tags or [])]
        
        relevant_sentiments = []
        max_impact = 0.0
        high_risk_alerts = []

        for item in all_news:
            relevant_sentiments.append(item["sentiment_score"])
            if item["macro_impact_score"] > max_impact:
                max_impact = item["macro_impact_score"]
            if item["macro_impact_score"] > 60 and item["sentiment_score"] < -30:
                high_risk_alerts.append(f"{item['category']}: {item['title']}")

        avg_sentiment = sum(relevant_sentiments) / len(relevant_sentiments) if relevant_sentiments else 0.0

        # Özel tag değerlendirmesi (Örn: Sinyal içinde FED_RATE veya WAR gelmişse)
        tag_penalty = 0.0
        if any("war" in t or "conflict" in t or "sanction" in t for t in custom_tags):
            tag_penalty += 35.0
            high_risk_alerts.append("CRITICAL: Sinyal içinde yüksek jeopolitik risk etiketi mevcut.")
        if any("rate" in t or "fed" in t or "inflation" in t for t in custom_tags):
            tag_penalty += 20.0

        # Makro Risk Skoru (0-100). Negatif duygu ve yüksek etki riski artırır.
        # Negatif sentiment (-100) -> Yüksek risk katkısı
        sentiment_risk = max(0.0, -avg_sentiment * 0.5) # 0 to 50
        macro_risk_score = min(100.0, (max_impact * 0.4) + sentiment_risk + tag_penalty)

        return {
            "average_sentiment": round(avg_sentiment, 2), # -100 to +100
            "max_macro_impact": round(max_impact, 2), # 0 to 100
            "macro_risk_score": round(macro_risk_score, 2), # 0 to 100
            "high_risk_alerts": high_risk_alerts[:3],
            "recent_news_count": len(all_news),
            "macro_state": "RISK_OFF" if macro_risk_score > 60 else ("RISK_ON" if avg_sentiment > 20 else "NEUTRAL")
        }

    def _get_fallback_macro_events(self) -> List[Dict[str, Any]]:
        return [
            {
                "title": "Küresel Ticaret Anlaşmaları ve Gümrük Vergisi Güncellemeleri İnceleme Altında",
                "summary": "Uluslararası ticaret görüşmeleri, gümrük kotaları ve tedarik zinciri güvenliği üzerine ikili müzakerelerle devam ediyor.",
                "published": "Yakın Zaman",
                "link": "#",
                "sentiment_score": 15.0,
                "macro_impact_score": 35.0,
                "category": "GEOPOLITICAL_TRADE",
                "keywords_matched": ["agreement", "tariff", "trade"]
            },
            {
                "title": "Merkez Bankaları Enflasyon ve Likidite Görünümünü İzliyor",
                "summary": "Para politikası kurulu üyeleri en son makroekonomik göstergeleri ve piyasa koşullarını değerlendiriyor.",
                "published": "Yakın Zaman",
                "link": "#",
                "sentiment_score": -5.0,
                "macro_impact_score": 50.0,
                "category": "CENTRAL_BANK_MONETARY",
                "keywords_matched": ["inflation", "rate"]
            }
        ]

news_macro_feed = NewsMacroFeedService()
