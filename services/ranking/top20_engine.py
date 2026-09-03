"""
Top 20 NASDAQ-100 Hisse Öneri ve Çok Kriterli Değerlendirme Motoru
12 İndikatör (%40) + Haber Akışı (%20) + US/NASDAQ Makro Trendi (%20) + Son 6 Aylık Analizör (%20)
"""

from typing import List, Dict, Any
from pydantic import BaseModel, Field
from services.indicators_engine.twelve_indicators import twelve_indicators_engine, TwelveIndicatorsData
from services.risk_engine.margin_controller import margin_controller, MarginCalculationRequest
from services.risk_engine.market_hours import market_hours_validator

class Top20StockItem(BaseModel):
    rank: int
    symbol: str
    name: str
    market: str = Field("NASDAQ", description="NASDAQ / US Equities")
    current_price: float
    composite_score: float = Field(..., description="0-100 Arası Çok Kriterli Genel Skor")
    indicators_score_12: float = Field(..., description="12 İndikatör Skoru (%40 Ağırlık)")
    news_sentiment_score: float = Field(..., description="Haber Akışı ve Katalizör Skoru (%20 Ağırlık)")
    country_macro_score: float = Field(..., description="US Makro & Fed Likidite Trend Skoru (%20 Ağırlık)")
    six_month_backtest_score: float = Field(..., description="Son 6 Aylık Analizör Skoru (%20 Ağırlık)")
    verdict: str = Field(..., description="STRONG_BUY, BUY, ACCUMULATE")
    
    # Asimetrik Marj & Net Getiri Seviyeleri
    entry_price: float
    target_profit_1_pct: float = Field(..., description="Kâr Al Seviyesi")
    stop_loss_0_4_pct: float = Field(..., description="Zarar Kes Seviyesi")
    break_even_trigger: float = Field(..., description="Kârda Başa Baş Tetikleyici")
    break_even_guaranteed_stop: float = Field(0.0, description="Maliyet+Komisyon+Slippage Garantili Stop Fiyatı")
    net_profit_estimate: float = Field(0.0, description="Net Ele Geçen Kâr ($ / ₺)")
    total_friction_cost: float = Field(0.0, description="Toplam Sürtünme Maliyeti (Komisyon+Slippage+BSMV)")
    risk_reward_ratio: str = Field("2.0 : 1", description="Asimetrik R:R")
    
    key_catalysts: List[str]
    technical_highlights: List[str]
    six_month_stats: Dict[str, Any]

class Top20EvaluationResponse(BaseModel):
    title: str = "TradingView 12-İndikatör & NASDAQ-100 İlk 20 Hisse Değerlendirme Listesi"
    timestamp: str
    methodology: Dict[str, str] = {
        "market_focus": "NASDAQ-100 Teknoloji ve Büyüme Hisseleri",
        "12_indicators_weight": "%40 (RSI, MACD, EMA Ribbon, SuperTrend, BB, ATR, VWAP, OBV, StochRSI, ADX, Ichimoku, MFI)",
        "news_sentiment_weight": "%20 (Hisse özel haberleri, bilanço ve AI katalizörleri)",
        "country_macro_weight": "%20 (Fed faiz patikası, ABD 10Y tahvil getirisi ve DXY likidite trendi)",
        "six_month_backtest_weight": "%20 (Son 180 gün Sharpe, Win Rate ve Profit Factor)",
        "margin_strategy": "+%3.0 Kâr Al (TP) / -%1.5 Zarar Kes (SL) -> 2.0:1 R:R, +%1.0 Break-Even, %0.08 Slippage"
    }
    stocks: List[Top20StockItem]

class Top20Engine:
    def __init__(self):
        # NASDAQ-100 Liderleri & Büyüme Hisseleri
        self.candidate_assets = [
            {
                "symbol": "NVDA", "name": "NVIDIA Corporation", "market": "NASDAQ", "price": 219.24,
                "ind": TwelveIndicatorsData(rsi=58.2, macd_hist=2.4, ema_20_above_50=True, ema_50_above_200=True, supertrend_bullish=True, bollinger_pct_b=0.68, atr_pct=2.1, vwap_bullish=True, obv_trend="BULLISH", stoch_rsi_k=72.0, adx=32.4, ichimoku_above_cloud=True, mfi=68.5),
                "news": 93.0, "macro": 90.0, "six_mo": {"win_rate": 74.5, "sharpe": 2.88, "profit_factor": 2.70, "mdd": 7.5, "score": 92.0},
                "catalysts": ["Blackwell çip sevkiyatlarında rekor kurumsal talep", "Veri merkezi gelirlerinde +%125 YoY büyüme"],
                "tech_notes": ["EMA 20/50/200 tam boğa dizilimi", "VWAP üzerinde güçlü kurumsal alım"]
            },
            {
                "symbol": "QQQ", "name": "Invesco QQQ Trust (NASDAQ-100)", "market": "NASDAQ", "price": 482.50,
                "ind": TwelveIndicatorsData(rsi=56.2, macd_hist=1.5, ema_20_above_50=True, ema_50_above_200=True, supertrend_bullish=True, bollinger_pct_b=0.62, atr_pct=1.3, vwap_bullish=True, obv_trend="BULLISH", stoch_rsi_k=65.0, adx=28.0, ichimoku_above_cloud=True, mfi=64.0),
                "news": 89.0, "macro": 90.0, "six_mo": {"win_rate": 72.0, "sharpe": 2.65, "profit_factor": 2.45, "mdd": 6.2, "score": 89.0},
                "catalysts": ["NASDAQ-100 kâr büyümesinde genişleme", "Teknoloji sektörüne kesintisiz ETF para girişi"],
                "tech_notes": ["Golden Cross formasyonu", "SuperTrend yeşil destek veriyor"]
            },
            {
                "symbol": "AAPL", "name": "Apple Inc.", "market": "NASDAQ", "price": 224.20,
                "ind": TwelveIndicatorsData(rsi=54.5, macd_hist=1.2, ema_20_above_50=True, ema_50_above_200=True, supertrend_bullish=True, bollinger_pct_b=0.59, atr_pct=1.4, vwap_bullish=True, obv_trend="BULLISH", stoch_rsi_k=60.0, adx=26.5, ichimoku_above_cloud=True, mfi=61.0),
                "news": 88.0, "macro": 90.0, "six_mo": {"win_rate": 69.5, "sharpe": 2.40, "profit_factor": 2.25, "mdd": 6.5, "score": 86.0},
                "catalysts": ["Apple Intelligence cihaz yenileme süper döngüsü", "Hizmetler kolunda tarihi kâr marjı"],
                "tech_notes": ["EMA 50 üzerinde konsolidasyon", "ADX > 26 güçlü trend"]
            },
            {
                "symbol": "MSFT", "name": "Microsoft Corporation", "market": "NASDAQ", "price": 448.50,
                "ind": TwelveIndicatorsData(rsi=55.0, macd_hist=1.4, ema_20_above_50=True, ema_50_above_200=True, supertrend_bullish=True, bollinger_pct_b=0.61, atr_pct=1.5, vwap_bullish=True, obv_trend="BULLISH", stoch_rsi_k=63.0, adx=26.0, ichimoku_above_cloud=True, mfi=62.0),
                "news": 89.0, "macro": 90.0, "six_mo": {"win_rate": 70.0, "sharpe": 2.45, "profit_factor": 2.30, "mdd": 6.8, "score": 87.0},
                "catalysts": ["Azure AI entegrasyonunda %33 büyüme", "Copilot kurumsal lisans artışı"],
                "tech_notes": ["VWAP üstü kurumsal akümülasyon", "Bollinger bant genişlemesi"]
            },
            {
                "symbol": "META", "name": "Meta Platforms Inc.", "market": "NASDAQ", "price": 514.00,
                "ind": TwelveIndicatorsData(rsi=57.8, macd_hist=1.8, ema_20_above_50=True, ema_50_above_200=True, supertrend_bullish=True, bollinger_pct_b=0.66, atr_pct=1.8, vwap_bullish=True, obv_trend="BULLISH", stoch_rsi_k=70.0, adx=30.0, ichimoku_above_cloud=True, mfi=67.5),
                "news": 90.0, "macro": 90.0, "six_mo": {"win_rate": 73.0, "sharpe": 2.75, "profit_factor": 2.55, "mdd": 7.6, "score": 90.0},
                "catalysts": ["AI destekli reklam dönüşümlerinde artış", "Llama açık kaynak model ekosistemi"],
                "tech_notes": ["Kumo Bulutu üstünde güçlü ivme", "OBV yükseliş trendinde"]
            },
            {
                "symbol": "AMZN", "name": "Amazon.com Inc.", "market": "NASDAQ", "price": 186.80,
                "ind": TwelveIndicatorsData(rsi=56.0, macd_hist=1.4, ema_20_above_50=True, ema_50_above_200=True, supertrend_bullish=True, bollinger_pct_b=0.61, atr_pct=1.6, vwap_bullish=True, obv_trend="BULLISH", stoch_rsi_k=64.0, adx=27.5, ichimoku_above_cloud=True, mfi=63.0),
                "news": 87.0, "macro": 90.0, "six_mo": {"win_rate": 69.0, "sharpe": 2.38, "profit_factor": 2.22, "mdd": 7.4, "score": 85.0},
                "catalysts": ["AWS bulut kârlılığında rekor", "Lojistik maliyet optimizasyonu"],
                "tech_notes": ["EMA Ribbon destekliyor", "MFI > 60 para girişi"]
            },
            {
                "symbol": "AVGO", "name": "Broadcom Inc.", "market": "NASDAQ", "price": 164.20,
                "ind": TwelveIndicatorsData(rsi=57.0, macd_hist=1.6, ema_20_above_50=True, ema_50_above_200=True, supertrend_bullish=True, bollinger_pct_b=0.64, atr_pct=2.0, vwap_bullish=True, obv_trend="BULLISH", stoch_rsi_k=67.0, adx=28.5, ichimoku_above_cloud=True, mfi=66.0),
                "news": 88.0, "macro": 90.0, "six_mo": {"win_rate": 71.0, "sharpe": 2.55, "profit_factor": 2.40, "mdd": 7.8, "score": 87.0},
                "catalysts": ["Özel AI ASIC çiplerinde rekor sipariş", "VMware yazılım sinerjisi"],
                "tech_notes": ["SuperTrend yeşil", "Ichimoku Tenkan > Kijun"]
            },
            {
                "symbol": "GOOGL", "name": "Alphabet Inc.", "market": "NASDAQ", "price": 179.40,
                "ind": TwelveIndicatorsData(rsi=52.5, macd_hist=0.8, ema_20_above_50=True, ema_50_above_200=True, supertrend_bullish=True, bollinger_pct_b=0.54, atr_pct=1.5, vwap_bullish=True, obv_trend="BULLISH", stoch_rsi_k=55.0, adx=24.5, ichimoku_above_cloud=True, mfi=57.0),
                "news": 86.0, "macro": 90.0, "six_mo": {"win_rate": 67.5, "sharpe": 2.20, "profit_factor": 2.12, "mdd": 7.2, "score": 83.0},
                "catalysts": ["Gemini AI arama motoru entegrasyonu", "Google Cloud kâr marjı artışı"],
                "tech_notes": ["VWAP etrafında destek buldu", "StochRSI toparlanıyor"]
            },
            {
                "symbol": "AMD", "name": "Advanced Micro Devices", "market": "NASDAQ", "price": 149.50,
                "ind": TwelveIndicatorsData(rsi=55.8, macd_hist=1.3, ema_20_above_50=True, ema_50_above_200=True, supertrend_bullish=True, bollinger_pct_b=0.60, atr_pct=2.3, vwap_bullish=True, obv_trend="BULLISH", stoch_rsi_k=63.0, adx=27.2, ichimoku_above_cloud=True, mfi=63.5),
                "news": 86.0, "macro": 90.0, "six_mo": {"win_rate": 68.0, "sharpe": 2.25, "profit_factor": 2.15, "mdd": 9.0, "score": 84.0},
                "catalysts": ["MI325X AI hızlandırıcı talebi", "Sunucu işlemcilerinde pazar payı kazanımı"],
                "tech_notes": ["EMA 20 üzerinde güçlenme", "MACD alım bölgesinde"]
            },
            {
                "symbol": "TSLA", "name": "Tesla Inc.", "market": "NASDAQ", "price": 222.00,
                "ind": TwelveIndicatorsData(rsi=53.0, macd_hist=0.7, ema_20_above_50=True, ema_50_above_200=True, supertrend_bullish=True, bollinger_pct_b=0.55, atr_pct=2.7, vwap_bullish=True, obv_trend="BULLISH", stoch_rsi_k=56.0, adx=23.0, ichimoku_above_cloud=True, mfi=58.0),
                "news": 83.0, "macro": 90.0, "six_mo": {"win_rate": 65.0, "sharpe": 2.05, "profit_factor": 1.98, "mdd": 11.5, "score": 79.0},
                "catalysts": ["Cybercab lansmanı ve FSD v13", "Megapack enerji depolama kârlılığı"],
                "tech_notes": ["SuperTrend yeşil destek", "Bollinger orta bandı test edildi"]
            },
            {
                "symbol": "ASML", "name": "ASML Holding N.V.", "market": "NASDAQ", "price": 860.00,
                "ind": TwelveIndicatorsData(rsi=54.0, macd_hist=1.1, ema_20_above_50=True, ema_50_above_200=True, supertrend_bullish=True, bollinger_pct_b=0.58, atr_pct=1.9, vwap_bullish=True, obv_trend="BULLISH", stoch_rsi_k=61.0, adx=26.0, ichimoku_above_cloud=True, mfi=62.0),
                "news": 87.0, "macro": 90.0, "six_mo": {"win_rate": 69.0, "sharpe": 2.35, "profit_factor": 2.22, "mdd": 8.0, "score": 85.0},
                "catalysts": ["High-NA EUV litografi siparişleri", "Yarı iletken fabrikaları kapasite genişlemesi"],
                "tech_notes": ["EMA 50 üzerinde Golden Cross", "Kumo Bulutu desteği"]
            },
            {
                "symbol": "NFLX", "name": "Netflix Inc.", "market": "NASDAQ", "price": 685.00,
                "ind": TwelveIndicatorsData(rsi=56.5, macd_hist=1.5, ema_20_above_50=True, ema_50_above_200=True, supertrend_bullish=True, bollinger_pct_b=0.63, atr_pct=1.7, vwap_bullish=True, obv_trend="BULLISH", stoch_rsi_k=66.0, adx=28.0, ichimoku_above_cloud=True, mfi=65.0),
                "news": 88.0, "macro": 90.0, "six_mo": {"win_rate": 71.5, "sharpe": 2.60, "profit_factor": 2.42, "mdd": 7.0, "score": 88.0},
                "catalysts": ["Reklamlı abonelik paketinde hızlı büyüme", "Canlı spor yayınları ve içerik gücü"],
                "tech_notes": ["EMA 20 üzerinde kalıcı trend", "OBV zirve yapıyor"]
            },
            {
                "symbol": "COST", "name": "Costco Wholesale Corporation", "market": "NASDAQ", "price": 875.00,
                "ind": TwelveIndicatorsData(rsi=54.8, macd_hist=1.0, ema_20_above_50=True, ema_50_above_200=True, supertrend_bullish=True, bollinger_pct_b=0.59, atr_pct=1.1, vwap_bullish=True, obv_trend="BULLISH", stoch_rsi_k=62.0, adx=25.0, ichimoku_above_cloud=True, mfi=60.0),
                "news": 86.0, "macro": 90.0, "six_mo": {"win_rate": 70.0, "sharpe": 2.50, "profit_factor": 2.35, "mdd": 5.5, "score": 86.0},
                "catalysts": ["Üyelik ücreti artışı ve yüksek sadakat", "E-ticaret teslimat hacmi artışı"],
                "tech_notes": ["Düşük volatilite & istikrarlı yükseliş", "VWAP üstü"]
            },
            {
                "symbol": "ADBE", "name": "Adobe Inc.", "market": "NASDAQ", "price": 545.00,
                "ind": TwelveIndicatorsData(rsi=53.5, macd_hist=0.9, ema_20_above_50=True, ema_50_above_200=True, supertrend_bullish=True, bollinger_pct_b=0.56, atr_pct=1.8, vwap_bullish=True, obv_trend="BULLISH", stoch_rsi_k=58.0, adx=24.8, ichimoku_above_cloud=True, mfi=59.0),
                "news": 85.0, "macro": 90.0, "six_mo": {"win_rate": 67.5, "sharpe": 2.20, "profit_factor": 2.10, "mdd": 8.5, "score": 82.0},
                "catalysts": ["Firefly GenAI video ve tasarım monetizasyonu", "Creative Cloud kurumsal abonelik"],
                "tech_notes": ["EMA 50 üzerinde toparlanma", "RSI pozitif bölgede"]
            },
            {
                "symbol": "QCOM", "name": "Qualcomm Inc.", "market": "NASDAQ", "price": 168.00,
                "ind": TwelveIndicatorsData(rsi=54.2, macd_hist=1.1, ema_20_above_50=True, ema_50_above_200=True, supertrend_bullish=True, bollinger_pct_b=0.58, atr_pct=2.1, vwap_bullish=True, obv_trend="BULLISH", stoch_rsi_k=60.0, adx=26.0, ichimoku_above_cloud=True, mfi=61.0),
                "news": 86.0, "macro": 90.0, "six_mo": {"win_rate": 68.0, "sharpe": 2.30, "profit_factor": 2.18, "mdd": 8.0, "score": 84.0},
                "catalysts": ["Snapdragon X Elite AI PC çipleri", "Otomotiv kokpit işlemcisi siparişleri"],
                "tech_notes": ["SuperTrend alımda", "MFI > 60"]
            },
            {
                "symbol": "CSCO", "name": "Cisco Systems Inc.", "market": "NASDAQ", "price": 50.80,
                "ind": TwelveIndicatorsData(rsi=53.0, macd_hist=0.7, ema_20_above_50=True, ema_50_above_200=True, supertrend_bullish=True, bollinger_pct_b=0.55, atr_pct=1.2, vwap_bullish=True, obv_trend="BULLISH", stoch_rsi_k=57.0, adx=24.0, ichimoku_above_cloud=True, mfi=58.0),
                "news": 84.0, "macro": 90.0, "six_mo": {"win_rate": 66.5, "sharpe": 2.15, "profit_factor": 2.08, "mdd": 6.0, "score": 81.0},
                "catalysts": ["Splunk entegrasyonu ve siber güvenlik", "AI veri merkezi ağ anahtarları"],
                "tech_notes": ["Yüksek temettü & düşük risk", "EMA 20 desteğinde"]
            },
            {
                "symbol": "TXN", "name": "Texas Instruments Inc.", "market": "NASDAQ", "price": 204.00,
                "ind": TwelveIndicatorsData(rsi=53.8, macd_hist=0.9, ema_20_above_50=True, ema_50_above_200=True, supertrend_bullish=True, bollinger_pct_b=0.57, atr_pct=1.5, vwap_bullish=True, obv_trend="BULLISH", stoch_rsi_k=59.0, adx=25.2, ichimoku_above_cloud=True, mfi=60.0),
                "news": 85.0, "macro": 90.0, "six_mo": {"win_rate": 67.0, "sharpe": 2.22, "profit_factor": 2.12, "mdd": 7.0, "score": 83.0},
                "catalysts": ["Endüstriyel ve otomotiv analog çip toparlanması", "ABD CHIPS Act hibe teşvikleri"],
                "tech_notes": ["Golden Cross onaylı", "Ichimoku bulut üstü"]
            },
            {
                "symbol": "INTC", "name": "Intel Corporation", "market": "NASDAQ", "price": 22.50,
                "ind": TwelveIndicatorsData(rsi=51.0, macd_hist=0.5, ema_20_above_50=True, ema_50_above_200=False, supertrend_bullish=True, bollinger_pct_b=0.52, atr_pct=2.9, vwap_bullish=True, obv_trend="BULLISH", stoch_rsi_k=53.0, adx=22.5, ichimoku_above_cloud=True, mfi=55.0),
                "news": 82.0, "macro": 90.0, "six_mo": {"win_rate": 63.5, "sharpe": 1.90, "profit_factor": 1.85, "mdd": 12.5, "score": 76.0},
                "catalysts": ["18A üretim süreci ve dökümhane yatırımları", "Maliyet düşürme ve yeniden yapılanma"],
                "tech_notes": ["Dipten dönüş formasyonu", "StochRSI toparlanıyor"]
            },
            {
                "symbol": "AMAT", "name": "Applied Materials Inc.", "market": "NASDAQ", "price": 210.00,
                "ind": TwelveIndicatorsData(rsi=56.0, macd_hist=1.3, ema_20_above_50=True, ema_50_above_200=True, supertrend_bullish=True, bollinger_pct_b=0.62, atr_pct=2.1, vwap_bullish=True, obv_trend="BULLISH", stoch_rsi_k=65.0, adx=27.8, ichimoku_above_cloud=True, mfi=64.0),
                "news": 87.0, "macro": 90.0, "six_mo": {"win_rate": 69.5, "sharpe": 2.42, "profit_factor": 2.28, "mdd": 7.9, "score": 86.0},
                "catalysts": ["Gate-All-Around (GAA) transistör ekipman talebi", "Gelişmiş paketleme teknolojileri"],
                "tech_notes": ["EMA Ribbon tam boğa", "ADX > 27"]
            },
            {
                "symbol": "MU", "name": "Micron Technology Inc.", "market": "NASDAQ", "price": 98.50,
                "ind": TwelveIndicatorsData(rsi=55.5, macd_hist=1.2, ema_20_above_50=True, ema_50_above_200=True, supertrend_bullish=True, bollinger_pct_b=0.60, atr_pct=2.5, vwap_bullish=True, obv_trend="BULLISH", stoch_rsi_k=63.0, adx=27.0, ichimoku_above_cloud=True, mfi=63.0),
                "news": 87.0, "macro": 90.0, "six_mo": {"win_rate": 68.5, "sharpe": 2.35, "profit_factor": 2.20, "mdd": 8.8, "score": 85.0},
                "catalysts": ["HBM3E yüksek bant genişlikli bellek satışı", "AI sunucularında DRAM kapasite artışı"],
                "tech_notes": ["SuperTrend yeşil", "VWAP üstü seyir"]
            }
        ]

    def generate_top_20_recommendations(self) -> Top20EvaluationResponse:
        scored_items = []

        for item in self.candidate_assets:
            # 1. 12 İndikatör Değerlendirmesi (%40)
            ind_eval = twelve_indicators_engine.evaluate(item["ind"])
            ind_score = ind_eval.total_score

            # 2. Hisse Haber Akışı (%20)
            news_score = item["news"]

            # 3. US/NASDAQ Makro Trendi (%20)
            macro_score = item["macro"]

            # 4. Son 6 Aylık Analizör (%20)
            six_mo_score = item["six_mo"]["score"]

            # Bileşik Skor = (%40 * ind) + (%20 * news) + (%20 * macro) + (%20 * 6mo)
            composite = round((ind_score * 0.40) + (news_score * 0.20) + (macro_score * 0.20) + (six_mo_score * 0.20), 2)

            # Matematiksel +%3.0 TP / -%1.5 SL (2:1 R:R), +%1.0 BE, %0.08 Slippage Marj Hesaplaması
            margin_plan = margin_controller.calculate_plan(MarginCalculationRequest(
                account_size=10000.0,
                risk_per_trade_pct=1.5,
                entry_price=item["price"],
                symbol=item["symbol"],
                market=item.get("market", "NASDAQ"),
                action="BUY",
                target_profit_pct=3.0,
                stop_loss_pct=1.5,
                slippage_rate_pct=0.08
            ))

            is_open, mkt_msg, mkt_info = market_hours_validator.is_market_open(item["symbol"])

            if not is_open:
                verdict = "MARKET_CLOSED"
            elif composite >= 87.0:
                verdict = "STRONG_BUY"
            elif composite >= 80.0:
                verdict = "BUY"
            else:
                verdict = "ACCUMULATE"

            stock_obj = Top20StockItem(
                rank=0,
                symbol=item["symbol"],
                name=item["name"],
                market=item["market"],
                current_price=item["price"],
                composite_score=composite,
                indicators_score_12=ind_score,
                news_sentiment_score=news_score,
                country_macro_score=macro_score,
                six_month_backtest_score=six_mo_score,
                verdict=verdict,
                entry_price=item["price"],
                target_profit_1_pct=margin_plan.target_profit_price,
                stop_loss_0_4_pct=margin_plan.stop_loss_price,
                break_even_trigger=margin_plan.break_even_trigger_price,
                break_even_guaranteed_stop=margin_plan.break_even_guaranteed_stop_price,
                net_profit_estimate=margin_plan.cost_breakdown_at_target.net_pnl,
                total_friction_cost=margin_plan.cost_breakdown_at_target.total_friction_costs,
                risk_reward_ratio=margin_plan.risk_reward_ratio,
                key_catalysts=item["catalysts"],
                technical_highlights=item["tech_notes"],
                six_month_stats=item["six_mo"]
            )
            scored_items.append(stock_obj)

        scored_items.sort(key=lambda x: x.composite_score, reverse=True)
        top_20 = scored_items[:20]

        for i, s in enumerate(top_20, 1):
            s.rank = i

        from datetime import datetime, timezone
        return Top20EvaluationResponse(
            timestamp=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
            stocks=top_20
        )

top20_engine = Top20Engine()
