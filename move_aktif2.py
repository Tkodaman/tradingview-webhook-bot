with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

wallet_end = 48241
aktif_start = 50583
aktif_end = 58439

if 0 < wallet_end < aktif_start < aktif_end < len(text):
    aktif_html = text[aktif_start:aktif_end]
    
    # Remove from original location
    new_text = text[:aktif_start] + text[aktif_end:]
    
    # Insert right after wallet_end
    # We should add some spacing
    new_text = new_text[:wallet_end] + "\n\n    <!-- MOVED AKTIF POZISYONLAR -->\n    <div style='margin-bottom: 24px;'>\n" + aktif_html + "\n    </div>\n" + new_text[wallet_end:]
    
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("Successfully moved Aktif Pozisyonlar panel below Alpaca Wallet.")
else:
    print("Indices overlap or out of bounds.")
