"""
Sahte Kirılım (Fakeout) Tespit Modülü — Kazan-Kazan Risk Kalkani v2.0
=======================================================================
v2.0 Yenilikler:
- 4 test → 8 test
- 3 HIGH-RISK sinyal: tek basina HARD BLOCK
- Esik: 2/4 → 2/8 (daha hassas)
- Hacimsiz kırılım tekrar hard block

Zarar analizi:
- Toplam zararın %38+ sahte kirılımdan: FakeoutGuard v1 yetersizdi
- Temel sorun: vol<1.2 blogu soft hale getirilince hacimsiz kırılımlar gecti
"""

from dataclasses import dataclass
from core.logger import logger


@dataclass
class FakeoutResult:
    is_fakeout: bool
    reason: str
    confidence: float  # 0.0-1.0 arası fakeout olasılıgı


class FakeoutGuard:
    def __init__(self):
        self.min_volume_confirmation: float = 1.2
        self.cmf_min: float = 0.0
        self.stoch_overbought: float = 85.0

    def check(
        self,
        symbol: str,
        price: float,
        change_pct: float,
        vol_ratio: float,
        rsi: float,
        cmf: float,
        stoch_k: float,
        atr_pct: float = 1.5,
        body_ratio: float = 0.5,
        bid_ask_ratio: float = 0.5,
    ) -> FakeoutResult:
        fakeout_signals = 0
        max_signals = 8
        reasons = []

        # ============================================================
        # HIGH-RISK SINYALLER: Tek basina HARD BLOCK (is_fakeout = True)
        # ============================================================

        # HR1: Hacimsiz Kirılım — vol < 0.80 VE degisim > %1.5
        # Sahte kırılımın en guclu gostergesi: hacim olmadan fiyat cikmaz
        if vol_ratio < 0.80 and change_pct > 1.5:
            reason = f"[HR1] HACIMSIZ KIRILIM: Vol={vol_ratio:.2f}<0.80 + Chg={change_pct:.1f}%>1.5%"
            logger.warning(f"[FAKEOUT GUARD HR1] {symbol} {reason}")
            return FakeoutResult(is_fakeout=True, reason=reason, confidence=1.0)

        # HR2: FOMO Pump Hızı — tek tickte %15+ spike (Kural esnetildi - Agresif mod)
        # Manipülatif spike: haber/bot/wash trading — geri dönüş kaçınılmaz
        if change_pct >= 15.0 and vol_ratio < 1.5:
            reason = f"[HR2] FOMO PUMP SPIKE: Chg={change_pct:.1f}%>=15% hacim desteği yok"
            logger.warning(f"[FAKEOUT GUARD HR2] {symbol} {reason}")
            return FakeoutResult(is_fakeout=True, reason=reason, confidence=1.0)

        # HR3: Fitil Ağırlıklı Mum + Hacimsiz = Kesin Geri Dönüş
        # body_ratio < 0.20: mumun %80+ fitil, neredeyse hiç gövde yok
        if body_ratio < 0.20 and vol_ratio < 0.90 and change_pct > 0.5:
            reason = f"[HR3] FITIL+HACİMSİZ: Body={body_ratio:.2f}<0.20 Vol={vol_ratio:.2f}<0.90"
            logger.warning(f"[FAKEOUT GUARD HR3] {symbol} {reason}")
            return FakeoutResult(is_fakeout=True, reason=reason, confidence=0.95)

        # ============================================================
        # SOFT SINYALLER: 2+ sinyal = FAKEOUT (max_signals=8 icinden)
        # ============================================================

        # S1: CMF Uyumsuzlugu (Para akısı yok ama fiyat yukseliyor)
        if cmf <= self.cmf_min and change_pct > 1.0:
            fakeout_signals += 1
            reasons.append(f"CMF={cmf:.3f}<=0 (Para akısı yok)")

        # S2: Hacimsiz Kirılım (0.80-1.20 arası: soft uyarı)
        if 0.80 <= vol_ratio < self.min_volume_confirmation and change_pct > 0.8:
            fakeout_signals += 1
            reasons.append(f"Vol={vol_ratio:.2f}<1.2 (Zayıf hacim)")

        # S3: Stochastic Asırı Alım + Yukselis = Gec Giris Tuzagı
        if stoch_k >= self.stoch_overbought and change_pct > 1.5:
            fakeout_signals += 1
            reasons.append(f"Stoch={stoch_k:.1f}>=85 asırı alım")

        # S4: RSI Asırı Alım + Yuksek Degisim = FOMO Tepe Tuzagı
        if rsi >= 72.0 and change_pct >= 2.5:
            fakeout_signals += 1
            reasons.append(f"RSI={rsi:.1f}>=72 + Chg={change_pct:.1f}% FOMO")

        # S5: CMF Negatif Momentum — kurumsal satış sırasında sıçrama
        # (S1'den farklı: daha güçlü negatif CMF seviyesi)
        if cmf < -0.08 and change_pct > 0.5:
            fakeout_signals += 1
            reasons.append(f"CMF={cmf:.3f}<-0.08 kurumsal satış")

        # S6: Orderbook Satıcı Baskısı + Yukselis
        # Bid oranı dusukken fiyat cıkıyorsa = spoofing riski
        if bid_ask_ratio < 0.42 and change_pct > 1.0:
            fakeout_signals += 1
            reasons.append(f"OBK={bid_ask_ratio:.2f}<0.42 satıcı baskısı")

        # S7: Stoch Overbought + Zayıf Hacim (combo)
        if stoch_k >= 75.0 and vol_ratio < 1.0 and change_pct > 1.0:
            fakeout_signals += 1
            reasons.append(f"Stoch={stoch_k:.1f}>=75 + Vol={vol_ratio:.2f}<1.0")

        # S8: Fitil Mum Genel (HR3'ten daha az sert)
        if 0.20 <= body_ratio < 0.32 and change_pct > 1.2:
            fakeout_signals += 1
            reasons.append(f"Body={body_ratio:.2f}<0.32 fitil agirlikli")

        # Sonuc hesapla
        confidence = round(fakeout_signals / max_signals, 2)
        is_fakeout = fakeout_signals >= 2  # 2+ soft sinyal = fakeout

        if is_fakeout:
            reason_str = " | ".join(reasons)
            logger.warning(
                f"[FAKEOUT GUARD v2] {symbol} SAHTE KIRILIM ({fakeout_signals}/{max_signals}, %{confidence*100:.0f}): {reason_str}"
            )
            return FakeoutResult(is_fakeout=True, reason=reason_str, confidence=confidence)

        if fakeout_signals == 1:
            logger.debug(f"[FAKEOUT GUARD v2] {symbol} 1 suphe sinyali (gecti): {' | '.join(reasons)}")

        return FakeoutResult(is_fakeout=False, reason="", confidence=confidence)


fakeout_guard = FakeoutGuard()

