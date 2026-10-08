import time
import requests
import sys
import os
from dotenv import load_dotenv

load_dotenv()
from services.engine.telegram_notifier import send_telegram_alert

ENTRY_PRICE = 23.70
INVESTMENT_TL = 20000.0
TIA_AMOUNT = INVESTMENT_TL / ENTRY_PRICE  # ~843.88 TIA

TP1_PRICE = 24.85
SL_PRICE = 22.90

CHECK_INTERVAL_SEC = 60
REPORT_INTERVAL_SEC = 40 * 60  # 40 dakika

def get_tia_try_price():
    try:
        response = requests.get('https://api.btcturk.com/api/v2/ticker?pairSymbol=TIA_TRY', timeout=10)
        data = response.json()
        if data.get('success') and len(data.get('data', [])) > 0:
            return float(data['data'][0]['last'])
    except Exception as e:
        print(f"API Hatası: {e}")
    return None

if __name__ == "__main__":
    start_msg = (
        "🦅 <b>YÜCE DİVAN - NİŞANCI PUSUSU GÜNCELLENDİ</b>\n\n"
        f"💰 Sermaye: <b>{INVESTMENT_TL:,.2f} TL</b>\n"
        f"🎯 Giriş Maliyeti: <b>{ENTRY_PRICE} TL</b>\n"
        f"📦 Alınan Miktar: <b>{TIA_AMOUNT:.2f} TIA</b>\n\n"
        f"📈 Kâr Hedefi (TP1): <b>{TP1_PRICE} TL</b>\n"
        f"🛑 Stop-Loss: <b>{SL_PRICE} TL</b>\n\n"
        "⏱️ Karargaha her 40 dakikada bir detaylı <b>Durum Raporu (PnL)</b> geçilecektir."
    )
    send_telegram_alert(start_msg)
    print("TIA Tracker Updated started...")
    
    last_report_time = time.time()
    
    while True:
        price = get_tia_try_price()
        if price is not None:
            current_time = time.time()
            pnl_tl = (price - ENTRY_PRICE) * TIA_AMOUNT
            pnl_pct = ((price - ENTRY_PRICE) / ENTRY_PRICE) * 100.0
            
            # 1. Hedef Kontrolü (Anında)
            if price >= TP1_PRICE:
                msg = (
                    "🚀 <b>TAARRUZ BAŞARILI! (TP1 VURULDU)</b>\n\n"
                    f"🎯 TIA/TRY Fiyatı: <b>{price} TL</b>\n"
                    f"💵 Net Kâr: <b>+{pnl_tl:,.2f} TL (+%{pnl_pct:.2f})</b>\n\n"
                    "BtcTurk kâr alım hedefine ulaştı. Kârınızı realize edin Komutanım!"
                )
                send_telegram_alert(msg)
                print("TP1 hit. Exiting.")
                break
                
            elif price <= SL_PRICE:
                msg = (
                    "🛑 <b>KALKAN PARÇALANDI! (STOP-LOSS VURULDU)</b>\n\n"
                    f"📉 TIA/TRY Fiyatı: <b>{price} TL</b>\n"
                    f"🩸 Net Zarar: <b>{pnl_tl:,.2f} TL (%{pnl_pct:.2f})</b>\n\n"
                    "Trend bozuldu ve zarar-kes noktasına ulaşıldı. Acil tahliye önerilir."
                )
                send_telegram_alert(msg)
                print("SL hit. Exiting.")
                break
                
            # 2. Periyodik Durum Raporu (40 dk'da bir)
            if (current_time - last_report_time) >= REPORT_INTERVAL_SEC:
                durum_icon = "🟢" if pnl_pct >= 0 else "🔴"
                msg = (
                    f"📡 <b>NİŞANCI RUTİN RAPORU (TIA/TRY)</b>\n\n"
                    f"📊 Güncel Fiyat: <b>{price} TL</b>\n"
                    f"🎯 Maliyet: <b>{ENTRY_PRICE} TL</b>\n"
                    f"{durum_icon} Anlık PnL: <b>{pnl_tl:+,.2f} TL ({pnl_pct:+,.2f}%)</b>\n\n"
                    f"📈 TP1'e Uzaklık: <b>% {((TP1_PRICE - price)/price)*100:.2f}</b>\n"
                    f"🛑 SL'ye Uzaklık: <b>% {((price - SL_PRICE)/price)*100:.2f}</b>"
                )
                send_telegram_alert(msg)
                last_report_time = current_time
                print("Periodic report sent.")
                
        time.sleep(CHECK_INTERVAL_SEC)
