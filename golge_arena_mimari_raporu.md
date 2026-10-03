# 🟢 Gölge Arena (Shadow Arena): Otonom Eğitim ve Cüretkâr Sınama Modülü

## 1. Vizyon ve Amacın Yeniden Tanımlanması
Gölge Arena, botun yalnızca hazır piyasa fırsatlarını beklediği pasif bir sistem değil; **kendi sınırlarını test ettiği, piyasayla ve kendisiyle yarıştığı, cüretkâr (vur-kaç, balina sörfü) hamleler yaparak tecrübe kazandığı aktif bir laboratuvardır.** Gerçek (aktif) pozisyon riski almadan, otonom zekanın (ML) piyasanın nabzını tutmasını ve gelecekteki gerçek işlemler için keskin bir "öngörü (foresight)" oluşturmasını sağlar.

## 2. Sistemin Yeni Karakteristiği
*   **Varlık Havuzu (Deney Alanı):** Sadece tetiklenen alarmlarla yetinilmez. Kripto, BİST ve NASDAQ'da yüksek volatiliteye sahip varlıklardan (örn: ONDO, VRT, TSLA, PEPE) özel bir havuz oluşturulur.
*   **Cüretkâr Hamleler:** Sistem, gerçek sermayeyle girmeye çekineceği yüksek riskli hareketlere (Whale-Surf, Squeeze kırılımları) bu arenada korkusuzca girer.
*   **Kısa Döngü (Max 8 Saat):** Öğrenme hızını maksimize etmek için bu işlemler uzun vade yatırımı olarak tutulmaz. Maksimum 8 saat içinde kâr (TP) veya zarar (SL) ile sonuçlandırılarak hafızaya (tecrübeye) dönüştürülür.
*   **İç Ses ve Öz Eleştiri:** Bot, yaptığı bu cüretkâr hamlelerin *nedenini* (iç sesini), girdiği ve çıktığı zamanları, hata yaptıysa "nerede yanıldığını" açıkça komutana (admine) raporlar.

## 3. Komite ve Mimar Tarafından Uygulanan Revizyonlar (Teknik Çıktılar)
1.  **Otonom Tarayıcı (Active Scanner):** `main.py` içerisindeki tarayıcı, webhook beklemeden piyasayı bizzat koklayacak ve ML puanı 40'ı geçen her fırtınaya atlayacak şekilde kodlandı.
2.  **Dashboard Yansıması (UI UI):** Komuta merkezine (dashboard) sadece donuk istatistikler değil; botun "Bu varlıkta balina akışı gördüm, riskli ama deniyorum" dediği anlık düşünce yapısını ve işlemin matematiksel sonuçlarını (Giriş, Çıkış, SL, TP, Süre, PnL) birleştiren hibrit bir **Otonom İç Ses Paneli** entegre edildi.
3.  **Tecrübe Birikimi (Deneyim Havuzu):** Her günün, haftanın ve ayın sonunda bu arenada dökülen kanlar (zararlar) ve kazanılan zaferler, botun ana Risk Motoruna (Risk Engine) bir "Baskı/Rejim" tecrübesi olarak yansıyacak. (Zarar Rejimi / Güçlü Boğa kalkanları bu verilerle esneyecek).

*Bu belge, Konsey'in ve Mimar Komitesinin mutlak yürütme kararıdır.*
