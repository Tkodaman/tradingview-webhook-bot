import re
import os
import json

file_path = 'templates/dashboard.html'
try:
    with open(file_path, 'r', encoding='utf-8') as f:
        html = f.read()

    print("=== YAZILIM MİMARİSİ VE UI AJANLARI KONSEY RAPORU ===")
    print("1. STATİK VE DOM ANALİZİ:")
    
    # Check for empty links that might act as dead buttons
    empty_hrefs = len(re.findall(r'href=[\"\']#[\"\']', html))
    print(f" - Tespit: {empty_hrefs} adet işlevsiz (ölü) bağlantı bulundu.")
    
    # Check for missing dynamic data bindings
    ws_endpoints = set(re.findall(r'new WebSocket\([`\'\"](.*?)[`\'\"]\)', html))
    fetch_endpoints = set(re.findall(r'fetch\([`\'\"](.*?)[`\'\"]', html))
    
    print(f" - Tespit: WebSocket Bağlantıları: {ws_endpoints}")
    print(f" - Tespit: Fetch (REST API) İstekleri: {len(fetch_endpoints)} adet endpoint kullanılıyor.")
    
    # Look for error logging or try/catch blocks in JS
    catch_blocks = len(re.findall(r'catch\s*\((.*?)\)', html))
    print(f" - JS Hata Yakalama (Try/Catch) Blokları: {catch_blocks}")
    
    # Search for known "Paneller yansımıyor" issues
    # Usually this happens if a variable is undefined or a JSON parse fails silently
    if 'console.error' not in html:
        print(" - KRİTİK EKSİK: Arayüzde konsol hata loglama mekanizması (console.error) yetersiz.")
        
    print("\n2. YARGI KOMİTESİ HÜKMÜ:")
    print(" - 'Çalışmayan Yansıma Panelleri' genellikle WebSocket koptuğunda reconnect (yeniden bağlanma) döngüsünün olmamasından veya gelen verinin DOM elementini bulamamasından (ID uyuşmazlığı) kaynaklanır.")
    print(" - Backtest ve simülasyon panelleri için özel bir veri doğrulama (validation) katmanı eklenmelidir.")

except Exception as e:
    print(f"HATA: {e}")
