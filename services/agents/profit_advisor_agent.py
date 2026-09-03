"""
Kâr Optimizasyon & Strateji İlerleme Ajanı (ProfitAdvisorAgent)
================================================================
Botun iç dünyasından — ExperienceMemory, TradeJournal, SkillAudit ve
PnL geçmişini okuyarak somut ve aksiyona dönük kâr artırma önerileri üretir.

Öneri kategorileri:
  1. Pariite Optimizasyonu  (hangi semboller daha kârlı?)
  2. Strateji Rotasyonu     (MOMENTUM mu, MEAN_REVERSION mu daha fazla kazandırıyor?)
  3. Zaman Penceresi        (haftanın hangi günü / saati daha iyi sonuç?)
  4. Lot Boyutu Önerisi     (kazanç serisinde artır, kayıp serisinde küçült)
  5. Skill Zayıflık Raporu  (hangi indikatör kararları hep yanlış gidiyor?)
"""

from datetime import datetime, timezone
from typing import Dict, Any, List
from core.logger import logger


class ProfitAdvisorAgent:
    """
    Botun iç verilerini analiz ederek somut kâr büyütme önerileri üreten ajan.
    Herhangi bir dış API'ye bağlı değildir — tamamen iç hafızayı okur.
    """

    VERSION = "v1.0"

    def __init__(self):
        self._last_report_time: str = ""

    # ─────────────────────────────────────────────────────────────
    # ANA ANALİZ METODU
    # ─────────────────────────────────────────────────────────────
    def generate_full_report(self) -> Dict[str, Any]:
        """
        Tüm iç veri kaynaklarını okuyarak kapsamlı kâr önerisi raporu üretir.
        """
        from services.engine.experience_memory_engine import experience_memory_engine
        from services.engine.trade_journal_learning import trade_journal_engine
        from services.market_feed.live_stream import live_trade_manager

        logger.info("[PROFIT ADVISOR] Tam kâr analiz raporu başlatıldı...")
        self._last_report_time = datetime.now(timezone.utc).isoformat()

        # 1. Ham veri toplama
        trade_history = experience_memory_engine.trade_history
        learned_rules = experience_memory_engine.learned_rules
        open_positions = [p for p in live_trade_manager.positions.values() if p.status == "OPEN"]

        # 2. Bölümlü analizler
        parity_report   = self._analyze_parities(trade_history)
        strategy_report = self._analyze_strategies(trade_history)
        timing_report   = self._analyze_timing(trade_history)
        sizing_report   = self._analyze_sizing(trade_history, live_trade_manager)
        skill_report    = self._analyze_skill_weaknesses(learned_rules)
        next_actions    = self._generate_next_actions(parity_report, strategy_report, sizing_report)

        report = {
            "status": "success",
            "agent": "ProfitAdvisorAgent",
            "version": self.VERSION,
            "generated_at": self._last_report_time,
            "summary": self._build_executive_summary(trade_history, open_positions),
            "parity_optimization": parity_report,
            "strategy_rotation": strategy_report,
            "timing_analysis": timing_report,
            "position_sizing": sizing_report,
            "skill_weakness_report": skill_report,
            "actionable_next_steps": next_actions,
        }
        logger.info(f"[PROFIT ADVISOR] Rapor tamamlandı. {len(next_actions)} aksiyonel öneri üretildi.")
        return report

    # ─────────────────────────────────────────────────────────────
    # 1. YÖNETİCİ ÖZETİ
    # ─────────────────────────────────────────────────────────────
    def _build_executive_summary(self, history, open_positions) -> Dict[str, Any]:
        if not history:
            return {
                "total_trades": 0, "win_rate": 0, "net_pnl": 0,
                "profit_factor": 0, "open_positions": len(open_positions),
                "verdict": "Henüz kapalı işlem yok — sistem analiz için veri bekliyor."
            }

        wins   = [t for t in history if t.is_win]
        losses = [t for t in history if not t.is_win]
        net    = sum(t.pnl_amount for t in history)
        gross_win  = sum(t.pnl_amount for t in wins) if wins else 0
        gross_loss = abs(sum(t.pnl_amount for t in losses)) if losses else 1
        pf = round(gross_win / gross_loss, 2)
        wr = round(len(wins) / len(history) * 100, 1)

        if wr >= 65 and pf >= 2.0:
            verdict = "🚀 SİSTEM KÂRLı VE SAĞLIKLI — Lot boyutunu artırma zamanı."
        elif wr >= 50 and pf >= 1.2:
            verdict = "✅ SİSTEM KAZANÇ BÖLGESINDE — İnce ayar ile kâr artırılabilir."
        elif wr >= 40:
            verdict = "⚠️ DÜŞÜK WIN RATE — Strateji rotasyonu gerekiyor."
        else:
            verdict = "🔴 SİSTEM ZARARDA — Parametre optimizasyonu acil."

        return {
            "total_trades": len(history),
            "wins": len(wins),
            "losses": len(losses),
            "win_rate_pct": wr,
            "net_pnl_usd": round(net, 2),
            "profit_factor": pf,
            "open_positions": len(open_positions),
            "verdict": verdict,
        }

    # ─────────────────────────────────────────────────────────────
    # 2. PARİTE OPTİMİZASYONU
    # ─────────────────────────────────────────────────────────────
    def _analyze_parities(self, history) -> Dict[str, Any]:
        if not history:
            return {"status": "veri_yok", "top_symbols": [], "toxic_symbols": []}

        sym_map: Dict[str, List] = {}
        for t in history:
            sym_map.setdefault(t.symbol, []).append(t)

        stats = []
        for sym, trades in sym_map.items():
            wins = [t for t in trades if t.is_win]
            wr   = round(len(wins) / len(trades) * 100, 1)
            net  = round(sum(t.pnl_amount for t in trades), 2)
            avg  = round(net / len(trades), 2)
            stats.append({
                "symbol": sym, "total_trades": len(trades),
                "win_rate_pct": wr, "net_pnl": net, "avg_pnl_per_trade": avg
            })

        stats.sort(key=lambda x: x["net_pnl"], reverse=True)
        top      = [s for s in stats if s["net_pnl"] > 0][:5]
        toxic    = [s for s in stats if s["net_pnl"] < 0 or s["win_rate_pct"] < 35][:5]

        return {
            "top_symbols": top,
            "toxic_symbols": toxic,
            "recommendation": (
                f"En kârlı {len(top)} sembolde lot büyütün. "
                f"Toksik {len(toxic)} sembolde işlem duraklatın."
                if top else "Henüz yeterli veri yok."
            ),
        }

    # ─────────────────────────────────────────────────────────────
    # 3. STRATEJİ ROTASYONU
    # ─────────────────────────────────────────────────────────────
    def _analyze_strategies(self, history) -> Dict[str, Any]:
        if not history:
            return {"status": "veri_yok"}

        strategy_map: Dict[str, List] = {}
        for t in history:
            # lesson_learned alanında strateji tag'i arar
            tag = "MOMENTUM_BREAKOUT"
            ll  = (t.lesson_learned or "").upper()
            if "MEAN_REVERSION" in ll:
                tag = "MEAN_REVERSION"
            elif "ARBITRAGE" in ll:
                tag = "STATISTICAL_ARBITRAGE"
            strategy_map.setdefault(tag, []).append(t)

        results = []
        for strat, trades in strategy_map.items():
            wins = [t for t in trades if t.is_win]
            net  = round(sum(t.pnl_amount for t in trades), 2)
            wr   = round(len(wins) / len(trades) * 100, 1) if trades else 0
            results.append({
                "strategy": strat,
                "total_trades": len(trades),
                "win_rate_pct": wr,
                "net_pnl": net,
            })

        results.sort(key=lambda x: x["net_pnl"], reverse=True)
        best = results[0]["strategy"] if results else "—"
        worst = results[-1]["strategy"] if len(results) > 1 else "—"

        return {
            "breakdown": results,
            "best_strategy": best,
            "worst_strategy": worst,
            "recommendation": (
                f"'{best}' stratejisi en yüksek kâr üretti. "
                f"'{worst}' stratejisi zarar/düşük getiri bölgesinde — ağırlığını azaltın."
            ),
        }

    # ─────────────────────────────────────────────────────────────
    # 4. ZAMAN PENCERESİ ANALİZİ
    # ─────────────────────────────────────────────────────────────
    def _analyze_timing(self, history) -> Dict[str, Any]:
        if not history:
            return {"status": "veri_yok"}

        day_map: Dict[str, List] = {}
        hour_map: Dict[int, List] = {}
        for t in history:
            try:
                dt = datetime.fromisoformat(t.timestamp)
                day = dt.strftime("%A")   # Monday, Tuesday…
                hr  = dt.hour
                day_map.setdefault(day, []).append(t)
                hour_map.setdefault(hr,  []).append(t)
            except Exception:
                pass

        best_day = max(day_map, key=lambda d: sum(x.pnl_amount for x in day_map[d])) if day_map else "—"
        worst_day= min(day_map, key=lambda d: sum(x.pnl_amount for x in day_map[d])) if day_map else "—"
        best_hour= max(hour_map, key=lambda h: sum(x.pnl_amount for x in hour_map[h])) if hour_map else "—"

        return {
            "best_day": best_day,
            "worst_day": worst_day,
            "best_hour_utc": f"{best_hour}:00 UTC" if isinstance(best_hour, int) else best_hour,
            "recommendation": (
                f"'{best_day}' gününde ve {best_hour}:00 UTC saatinde işlemler daha kârlı. "
                f"'{worst_day}' günü pozisyon açmaktan kaçının veya lot küçültün."
            ),
        }

    # ─────────────────────────────────────────────────────────────
    # 5. LOT BOYUTU ÖNERİSİ
    # ─────────────────────────────────────────────────────────────
    def _analyze_sizing(self, history, live_trade_manager) -> Dict[str, Any]:
        from services.ai_agent.system_prompt import RISK_PARAMS

        base = RISK_PARAMS.get("base_portfolio_size_usd", 1000.0)
        max_pct = RISK_PARAMS.get("max_capital_per_trade_pct", 10.0)
        current_lot = round(base * max_pct / 100, 2)

        if not history:
            return {
                "current_lot_usd": current_lot,
                "recommendation": "Veri yok — mevcut lot ayarını koru.",
                "suggested_lot_usd": current_lot,
                "action": "HOLD"
            }

        last5 = history[-5:] if len(history) >= 5 else history
        recent_wins = sum(1 for t in last5 if t.is_win)
        streak_msg  = f"Son {len(last5)} işlemde {recent_wins} kâr / {len(last5)-recent_wins} zarar"

        if recent_wins >= 4:
            new_lot = round(current_lot * 1.20, 2)
            action  = "ARTIR"
            rec = f"🟢 {streak_msg} — Kazanç serisi! Lot %20 artırılabilir: ${current_lot} → ${new_lot}"
        elif recent_wins <= 1:
            new_lot = round(current_lot * 0.70, 2)
            action  = "KÜÇÜLT"
            rec = f"🔴 {streak_msg} — Kayıp serisi! Lot %30 küçültülmeli: ${current_lot} → ${new_lot}"
        else:
            new_lot = current_lot
            action  = "HOLD"
            rec = f"🟡 {streak_msg} — Nötr. Mevcut lot seviyesini koru: ${current_lot}"

        return {
            "current_lot_usd": current_lot,
            "suggested_lot_usd": new_lot,
            "action": action,
            "recent_streak_summary": streak_msg,
            "recommendation": rec,
        }

    # ─────────────────────────────────────────────────────────────
    # 6. SKILL ZAYIFLIK RAPORU
    # ─────────────────────────────────────────────────────────────
    def _analyze_skill_weaknesses(self, learned_rules) -> Dict[str, Any]:
        block_rules   = [r for r in learned_rules if r.get("type") == "BLOCK"]
        caution_rules = [r for r in learned_rules if r.get("type") == "CAUTION"]
        reward_rules  = [r for r in learned_rules if r.get("type") == "REWARD"]

        weaknesses = []
        for r in block_rules[:5]:
            weaknesses.append({
                "regime": r.get("cluster_key", "—"),
                "insight": r.get("insight", "—"),
                "severity": "BLOCK 🔴",
            })
        for r in caution_rules[:3]:
            weaknesses.append({
                "regime": r.get("cluster_key", "—"),
                "insight": r.get("insight", "—"),
                "severity": "CAUTION 🟡",
            })

        strengths = [r.get("cluster_key", "—") for r in reward_rules[:3]]

        return {
            "total_learned_rules": len(learned_rules),
            "block_rules_count": len(block_rules),
            "caution_rules_count": len(caution_rules),
            "reward_rules_count": len(reward_rules),
            "top_weaknesses": weaknesses,
            "proven_strengths": strengths,
            "recommendation": (
                f"{len(block_rules)} blok kuralı aktif — bu rejimlerde işlem açma. "
                f"{len(reward_rules)} ödül rejimi var — bu koşullarda lot büyüt."
            ),
        }

    # ─────────────────────────────────────────────────────────────
    # 7. AKSİYONEL SONRAKİ ADIMLAR
    # ─────────────────────────────────────────────────────────────
    def _generate_next_actions(self, parity, strategy, sizing) -> List[Dict[str, Any]]:
        actions = []

        # Lot aksiyonu
        if sizing.get("action") == "ARTIR":
            actions.append({
                "priority": 1,
                "category": "LOT_SIZING",
                "action": f"Lot boyutunu ${sizing['current_lot_usd']} → ${sizing['suggested_lot_usd']} çıkar",
                "impact": "YÜKSEK",
                "reason": sizing.get("recommendation", ""),
            })
        elif sizing.get("action") == "KÜÇÜLT":
            actions.append({
                "priority": 1,
                "category": "RISK_CONTROL",
                "action": f"Lot boyutunu ${sizing['current_lot_usd']} → ${sizing['suggested_lot_usd']} küçült",
                "impact": "YÜKSEK",
                "reason": sizing.get("recommendation", ""),
            })

        # Pariite aksiyonu
        top = parity.get("top_symbols", [])
        toxic = parity.get("toxic_symbols", [])
        if top:
            actions.append({
                "priority": 2,
                "category": "PARITY_FOCUS",
                "action": f"Odak semboller: {[s['symbol'] for s in top[:3]]}",
                "impact": "YÜKSEK",
                "reason": f"Bu semboller en yüksek net PnL üretiyor.",
            })
        if toxic:
            actions.append({
                "priority": 2,
                "category": "PARITY_BLACKLIST",
                "action": f"Duraklat / Azalt: {[s['symbol'] for s in toxic[:3]]}",
                "impact": "ORTA",
                "reason": f"Bu semboller zarar veya düşük win-rate üretiyor.",
            })

        # Strateji aksiyonu
        best = strategy.get("best_strategy")
        worst = strategy.get("worst_strategy")
        if best and best != worst:
            actions.append({
                "priority": 3,
                "category": "STRATEGY_ROTATION",
                "action": f"'{best}' stratejisine ağırlık ver, '{worst}' stratejisini kısıtla",
                "impact": "ORTA",
                "reason": strategy.get("recommendation", ""),
            })

        if not actions:
            actions.append({
                "priority": 1,
                "category": "MONITORING",
                "action": "Sistem veri toplamaya devam etsin — ilk 10 işlem sonrası tam analiz yapılabilir.",
                "impact": "BİLGİ",
                "reason": "Yeterli işlem verisi henüz mevcut değil.",
            })

        return actions


# Singleton
profit_advisor_agent = ProfitAdvisorAgent()
