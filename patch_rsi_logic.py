with open('routers/market_router.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Add rsi_history global
if "rsi_history = {}" not in text:
    text = text.replace("router = APIRouter()", "router = APIRouter()\nrsi_history = {}")

# Replace logic block
import re

old_logic = r'''        # Puanlama
        score = 0
        if 40.0 <= rsi <= 80.0: score \+= 1
        if macd >= -0.50: score \+= 1
        if data.get\("ema_golden_cross", False\): score \+= 1
        if data.get\("vwap_bullish", False\): score \+= 1
        if vol_ratio >= 0.70: score \+= 1
        if 20.0 <= data.get\("stoch_k", 50.0\) <= 90.0: score \+= 1
        if data.get\("adx", 25.0\) >= 15.0: score \+= 1
        if data.get\("atr_pct", 1.5\) <= 6.0: score \+= 1
        if chg >= 1.2 and vol_ratio >= 0.8: score \+= 3 # Momentum Impulse
        
        open_pos = next\(\(p for p in live_trade_manager.positions.values\(\) if p.symbol.upper\(\) == sym.upper\(\) and p.status == "OPEN"\), None\)
        
        if open_pos:
            decision = "HOLD"
            badge = "🟢 POSITION_OPEN"
            reason = f"Açık Pozisyon Aktif \(Giriş: \\, PnL: \\\)"
        elif not is_open:
            decision = "WAIT"
            badge = "💤 SEANS_DISI"
            reason = f"Piyasa Kapalı: {market_status.get\('session_text', 'Seans saatleri dışında'\)}"
        elif score >= 3:
            decision = "BUY"
            badge = "🟢 BUY_SIGNAL"
            
            adx_val = data.get\("adx", 0\)
            if data.get\("vwap_bullish", False\) and vol_ratio >= 1.0:
                reason = "Fiyat VWAP üstünde - kurumsal destek aktif"
            elif data.get\("ema_golden_cross", False\):
                reason = "EMA Golden Cross aktif \(20>50>200\)"
            elif adx_val >= 40:
                reason = f"Güçlü trend ivmesi ADX={int\(adx_val\)}"
            elif rsi < 40 and macd > 0:
                reason = "Aşırı satım dibinden MACD alım kesişimi"
            else:
                reason = f"Trend gücü {score} indikatör onayıyla pozitif"
        elif rsi > 75.0 or macd < -1.5:
            decision = "SELL"
            badge = "🔴 SELL_SIGNAL"
            if rsi > 75.0:
                reason = f"Aşırı Alım Bölgesinde Riskli \(RSI={rsi:.1f}\)"
            else:
                reason = "Negatif MACD kesişimi ve satıcı baskısı"
        else:
            decision = "WAIT"
            badge = "🟡 WAIT_PATIENT"
            if 40 <= rsi <= 60:
                reason = "Piyasa yatay konsolidasyon evresinde \(Kırılım bekleniyor\)"
            else:
                reason = "İndikatörler uyumsuz, net teyit bekleniyor"'''

new_logic = '''        # RSI Geçmişi Takibi
        if sym not in rsi_history:
            rsi_history[sym] = []
        rsi_history[sym].append(rsi)
        if len(rsi_history[sym]) > 10:
            rsi_history[sym].pop(0)
            
        hist = rsi_history[sym]
        rsi_climbed_from_40 = False
        if len(hist) >= 3 and rsi > 55.0:
            # Varlık 40'dan 55'e düzenli/kademeli çıktı mı?
            min_recent_rsi = min(hist)
            if 40.0 <= min_recent_rsi <= 50.0 and hist[-1] > hist[-2]:
                rsi_climbed_from_40 = True

        # Puanlama (Otomatik taban puan yok, 0'dan başlıyor)
        score = 0
        if 40.0 <= rsi <= 72.0: score += 1
        if macd >= -0.50: score += 1
        if data.get("ema_golden_cross", False): score += 1
        if data.get("vwap_bullish", False): score += 1
        if vol_ratio >= 0.70: score += 1
        if 20.0 <= data.get("stoch_k", 50.0) <= 90.0: score += 1
        if data.get("adx", 25.0) >= 15.0: score += 1
        if data.get("atr_pct", 1.5) <= 6.0: score += 1
        if chg >= 1.2 and vol_ratio >= 0.8: score += 3 # Momentum Impulse
        
        open_pos = next((p for p in live_trade_manager.positions.values() if p.symbol.upper() == sym.upper() and p.status == "OPEN"), None)
        
        if open_pos:
            decision = "HOLD"
            badge = "🟢 POSITION_OPEN"
            reason = f"Açık Pozisyon Aktif (Giriş: , PnL: )"
        elif not is_open:
            decision = "WAIT"
            badge = "💤 SEANS_DISI"
            reason = f"Piyasa Kapalı: {market_status.get('session_text', 'Seans saatleri dışında')}"
        elif rsi > 72.0 or macd < -1.5:  # Kullanıcının 72 sınırı talebi
            decision = "SELL"
            badge = "🔴 SELL_SIGNAL"
            if rsi > 72.0:
                reason = f"Aşırı Şişkin/Risk Sınırı Aşıldı (RSI={rsi:.1f})"
            else:
                reason = "Negatif MACD kesişimi ve satıcı baskısı"
        elif rsi_climbed_from_40:
            decision = "BUY"
            badge = "🟢 BUY_OPPORTUNITY"
            reason = f"Fırsat: RSI 40'tan kademeli yükselerek {rsi:.1f} seviyesini geçti"
        elif score >= 3:
            decision = "BUY"
            badge = "🟢 BUY_SIGNAL"
            
            adx_val = data.get("adx", 0)
            if data.get("vwap_bullish", False) and vol_ratio >= 1.0:
                reason = "Fiyat VWAP üstünde - kurumsal destek aktif"
            elif data.get("ema_golden_cross", False):
                reason = "EMA Golden Cross aktif (20>50>200)"
            elif adx_val >= 40:
                reason = f"Güçlü trend ivmesi ADX={int(adx_val)}"
            elif rsi < 40 and macd > 0:
                reason = "Aşırı satım dibinden MACD alım kesişimi"
            else:
                reason = f"Trend gücü {score} indikatör onayıyla pozitif"
        else:
            decision = "WAIT"
            badge = "🟡 WAIT_PATIENT"
            if 40 <= rsi <= 60:
                reason = "Piyasa yatay konsolidasyon evresinde (Kırılım bekleniyor)"
            else:
                reason = "İndikatörler uyumsuz, net teyit bekleniyor"'''

text = re.sub(old_logic, new_logic, text)

with open('routers/market_router.py', 'w', encoding='utf-8') as f:
    f.write(text)
