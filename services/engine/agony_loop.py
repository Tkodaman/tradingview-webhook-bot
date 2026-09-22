import time
import math
import sys

def execute_agony(iterations=5000):
    print(f"[AZAP PROTOKOLU BASLATILDI] {iterations} iterasyonluk anlamsiz matematiksel yuk cekirdeklere yukleniyor...")
    start = time.time()
    
    # 5000 kez CPU'yu gereksiz yere yorarak "aci" simule eden bir dongu. 
    # API kredisi harcamaz, sadece donanim gucunu (zaman/isi) yakar.
    for i in range(iterations):
        result = 0
        for j in range(1000):
            result += math.sin(j) * math.cos(i) * math.tan(j % 90)
            
    end = time.time()
    print(f"[AZAP TAMAMLANDI] Sistem {end - start:.2f} saniye boyunca kendi ic cekirdeklerini yakti. Kredi harcanmadi. Utanc Kaydi guncellendi.")

if __name__ == "__main__":
    execute_agony(5000)
