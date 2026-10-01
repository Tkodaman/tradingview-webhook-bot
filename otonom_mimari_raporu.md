# TIER-1 OTONOM TİCARET MİMARİSİ (Astra-6 V2.0 - SOTA Edition)

Bu doküman, klasik sinyal botlarının ötesine geçerek tamamen otonom, çok boyutlu veri analizi yapan ve kurumsal fon (Hedge Fund) mantığıyla çalışan yeni nesil ticaret motorunun iş akışını tanımlar.

## 🧠 Karar Alma ve İş Akışı Hiyerarşisi

Sistem, bir işleme (BUY) girmeden önce sırasıyla aşağıdaki filtre ve güvenlik duvarlarından geçmek zorundadır. Herhangi bir aşamada onay alınamazsa süreç **NO-TRADE (İşlem Yok)** ile sonlanır.

### AŞAMA 1: Otonom Veri Toplama (Sıfır Gecikme)
Bot her 60 saniyede bir aşağıdaki kaynaklardan anlık veri hasadı yapar:
1. **Spot Fiyat ve İndikatörler:** TradingView Scanner API üzerinden (1 Saatlik RSI, MACD, CMF, ADX, ATR vb.)
2. **Türev Piyasası Verileri:** `ccxt` kütüphanesi üzerinden Binance Futures Açık Pozisyon (Open Interest) ve Fonlama Oranları (Funding Rate).

### AŞAMA 2: Fraktal Zaman Uyum Filtresi (Multi-Timeframe Matrix)
* **Kural:** 1 Saatlik (1h) grafikte güçlü bir alım sinyali gelse bile, 4 Saatlik (4h) ve Günlük (1D) grafiklerde genel trend düşüş yönündeyse (EMA200 altındaysa), bu hareket "Ölü Kedi Sıçraması" kabul edilir ve reddedilir.
* **Geçiş Şartı:** Okların tümü (Kısa, Orta ve Uzun Vade) aynı yönü göstermelidir.

### AŞAMA 3: Hacim ve Squeeze (Baskı) Sniping
* **Kural 1 (Balina Ayak İzi):** Son 1 saatlik hacim, geçmiş 20 saatin ortalamasının en az 2 katı (Volume Ratio > 2.0) olmalıdır.
* **Kural 2 (Short Squeeze Radarı):** Fiyat artarken, Fonlama Oranı (Funding Rate) aşırı negatifse, içeride sıkışan açığa satışçıların (shorter) likidite olacağı öngörülür ve işlem için ekstra "Agresif Giriş" puanı verilir.

### AŞAMA 4: Dinamik Kasa Yönetimi (Kelly Criterion)
* **Kural:** Sistemin geçmiş başarı oranına ve anlık piyasa oynaklığına (ATR) göre işleme girilecek miktar formülize edilir.
* **Uygulama:** Sinyal "Kusursuz" (A+ Setup) ise kasanın %10'u, sinyal "Riskli ama Olumlu" (B Setup) ise kasanın sadece %2'si riske edilir.

### AŞAMA 5: Yürütme ve Kalkanlar (Execution & Guardrails)
Tetik çekilip emir borsaya iletildiğinde, şu kalkanlar saniyesinde devreye girer:
1. **%2 Hard Stop-Loss:** Piyasa ne yaparsa yapsın, pozisyon %2 eksiyse anında acil çıkış yapılır.
2. **Break-Even İzleyen Kâr:** Kâr %2'yi gördüğü an, Stop-Loss noktası "Giriş Fiyatı"na (0 zarar) çekilir. Kriptoda masada kazanılmış para asla geri verilmez.

---

## 🏗️ Mimari Entegrasyon Planı
Bu yapıyı sisteme entegre etmek için oluşturulacak yeni motor: `services/engine/autonomous_loop.py`

Bu modül `main.py` üzerine arka plan görevi (Background Task) olarak eklenecek ve web sunucusundan tamamen bağımsız, kendi izole evreninde çalışacaktır.
