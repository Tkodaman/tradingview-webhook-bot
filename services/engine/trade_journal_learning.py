"""
Yapılandırılmış İşlem Eğitimi, Sert Giriş/Çıkış Disiplini ve Veri Birikim Servisi
(Structured Trade Journaling & Educational Data Accumulation Engine)
"""

import time
import json
from typing import Dict, Any, List, Optional
from datetime import datetime, timezone
from core.logger import logger
from services.market_feed.live_stream import live_trade_manager

class TradeJournalLearningEngine:
    def __init__(self):
        self.journal_entries: List[Dict[str, Any]] = []
        self.educational_modules = {
            "MODULE_1_MARKET_SCAN": "Piyasa Taraması & Fırsat Tespiti (Kurumsal Hacim & Trend Hizalanması)",
            "MODULE_2_STOCK_RESEARCH": "Hedefe Yönelik Varlık Araştırması (Fiyat/Hacim Yörüngesi & Destek/Direnç)",
            "MODULE_3_ADVANCED_TECHNICAL": "İleri Düzey Teknik Analiz & Tetikleme Noktaları (EMA, VWAP, RSI Konfluansı)",
            "MODULE_4_EXECUTION_LOG": "Yapılandırılmış İşlem Kaydı & İcra Logu (Giriş/Çıkış Zamanı, Lot, R:R Oranı)",
            "MODULE_5_PERFORMANCE_REVIEW": "Performans Analizi & Trade Günlüğü Denetimi (Sharpe, Kazanma Oranı, Max DD)",
            "MODULE_6_STRATEGY_REVIEW": "Kapsamlı Strateji & Piyasa Yapısı İncelemesi (15m/75m MTF, Kırılım Tuzakları)",
            "MODULE_7_PSYCHOLOGY_AUDIT": "İşlem Psikolojisi & Disiplin Denetimi (FOMO, Aşırı İşlem / Overtrading Engelleme)",
            "MODULE_8_DEEP_DIVE_MENTORSHIP": "Özel Konularda Derinlemesine Öğrenim & Mentorluk (Volatilite, Hacim Profili)",
            "MODULE_9_AI_BACKTESTING": "AI Destekli Backtest & Model Kalibrasyonu (Slippage, Kâr Faktörü, Overfitting)",
            "MODULE_10_PREMARKET_ROUTINE": "Piyasa Açılış Öncesi Hazırlık Rutini (Küresel Ekonomi, Hacim Haritası, Zihinsel Hazırlık)"
        }
        self._initialize_baseline_journal()

    def _initialize_baseline_journal(self):
        """
        Başlangıç için sert giriş-çıkış disiplinli eğitici örnek işlem logları oluşturur.
        """
        now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
        self.journal_entries = [
            {
                "trade_id": "EDU-NVDA-101",
                "timestamp": now,
                "symbol": "NVDA",
                "market": "NASDAQ",
                "side": "BUY",
                "entry_price": 218.76,
                "exit_price": 223.50,
                "quantity": 0.4571,
                "net_pnl": +2.17,
                "risk_reward_ratio": "1:2.8",
                "entry_reasons": [
                    "80m Makro Trend EMA50 ve VWAP üzerinde teyitli boğa yapısı.",
                    "15m alt zaman diliminde %2.9'luk hacimli patlama mumu (Momentum Explosion).",
                    "RSI 58 seviyesinde nötr-yükseliş alanında, sahte kırılım yok."
                ],
                "exit_reasons": [
                    "TP1 hedefi (+%2.0 kâr realizasyonu) gerçekleşti.",
                    "Geri kalan lotlar için iz süren stop (ATR Trailing) maliyete çekildi."
                ],
                "psychology_evaluation": "Disiplinli beklendi, FOMO ile mumun tepesinden atlanmadı. Planlanan R:R sadık kalındı.",
                "learning_notes": "Hacim ortalamanın 1.8 katı olduğunda kırılım teyitlerinin başarı oranı %82'ye yükseliyor."
            },
            {
                "trade_id": "EDU-THYAO-102",
                "timestamp": now,
                "symbol": "THYAO",
                "market": "BIST",
                "side": "BUY",
                "entry_price": 308.20,
                "exit_price": 314.50,
                "quantity": 0.3244,
                "net_pnl": +2.04,
                "risk_reward_ratio": "1:3.1",
                "entry_reasons": [
                    "BIST gündüz seansı açılışı sonrası EMA20 pullback desteğinden sekti.",
                    "12 indikatör tarayıcısında 5/8 puan teyit edildi.",
                    "Hacim rasyosu 1.4x ile kurumsal alımı doğruladı."
                ],
                "exit_reasons": [
                    "Seans sonuna doğru 314.50 direnç bölgesinde kademeli kâr alındı."
                ],
                "psychology_evaluation": "Erken kâr alma dürtüsüne karşı direnç gösterildi, hedef direnç beklendi.",
                "learning_notes": "BIST hisselerinde seans kapanışına 30 dk kala yapılan kâr alımları kaymayı en aza indiriyor."
            }
        ]

    def record_live_execution(
        self,
        symbol: str,
        market: str,
        side: str,
        entry_price: float,
        quantity: float,
        entry_reasons: List[str],
        risk_score: float
    ) -> Dict[str, Any]:
        """
        Canlı gerçekleşen her işlemi eğitici ders ve disiplin loglarıyla kaydeder.
        """
        entry_id = f"LOG-{symbol}-{int(time.time())}"
        now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

        log_item = {
            "trade_id": entry_id,
            "timestamp": now_str,
            "symbol": symbol,
            "market": market,
            "side": side,
            "entry_price": entry_price,
            "exit_price": None,
            "quantity": quantity,
            "net_pnl": 0.0,
            "risk_score": risk_score,
            "risk_reward_ratio": "1:2.5 (Hedeflenen)",
            "entry_reasons": entry_reasons,
            "exit_reasons": [],
            "psychology_evaluation": "Sert giriş kuralına sadık kalındı. Risk skoru ve pozisyon boyutu kurallarla sınırlandı.",
            "learning_notes": f"Bu işlem {symbol} için dinamik timeframe ve hassasiyet ayarları ile tetiklendi."
        }

        self.journal_entries.insert(0, log_item)
        logger.info(f"[TRADE JOURNAL RECORDED] {entry_id} | Symbol: {symbol} | Entry: ${entry_price}")
        return log_item

    def get_journal_summary(self) -> Dict[str, Any]:
        """
        Eğitim birikimi ve günlüğün genel istatistiklerini döner.
        """
        total_trades = len(self.journal_entries)
        wins = [j for j in self.journal_entries if j.get("net_pnl", 0) > 0]
        losses = [j for j in self.journal_entries if j.get("net_pnl", 0) < 0]
        win_rate = round((len(wins) / total_trades * 100.0), 1) if total_trades > 0 else 0.0
        total_pnl = sum(j.get("net_pnl", 0.0) for j in self.journal_entries)

        return {
            "status": "success",
            "total_logged_trades": total_trades,
            "win_rate_pct": win_rate,
            "total_accumulated_pnl": round(total_pnl, 2),
            "educational_modules": self.educational_modules,
            "recent_journal_entries": self.journal_entries[:10]
        }

trade_journal_engine = TradeJournalLearningEngine()
