with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx_alpaca = text.find('ALPACA REAL-TIME EQUITY')
if idx_alpaca != -1:
    print(f"ALPACA found at index: {idx_alpaca}")
    # Find the container bounds for ALPACA
    start_alpaca = text.rfind('<div class="stat-grid"', 0, idx_alpaca)
    print(f"ALPACA start container: {start_alpaca}")
else:
    print("ALPACA not found!")

idx_aktif = text.find('Aktif A')
if idx_aktif != -1:
    print(f"Aktif found at index: {idx_aktif}")
else:
    print("Aktif not found!")
