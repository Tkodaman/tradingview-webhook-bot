with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx_wallet = text.find('class="wallet-bar"')
# Find closing div of wallet-bar
div_count = 0
in_div = False
i = idx_wallet
end_wallet = -1

while i < len(text):
    if text[i:i+4] == '<div':
        div_count += 1
        in_div = True
    elif text[i:i+6] == '</div>':
        div_count -= 1
        if in_div and div_count == 0:
            end_wallet = i + 6
            break
    i += 1

print(f"Wallet end index: {end_wallet}")

idx_aktif = text.find('Aktif A')
start_aktif = text.rfind('<div class="panel"', 0, idx_aktif)
aktif_end_match = __import__('re').search(r'<div class="(panel|two-col-grid|main-grid|future-panel)"', text[idx_aktif:])
if aktif_end_match:
    end_aktif = idx_aktif + aktif_end_match.start()
else:
    end_aktif = len(text)

print(f"Aktif start: {start_aktif}, end: {end_aktif}")
