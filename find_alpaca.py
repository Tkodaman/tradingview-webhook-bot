import re
with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx_alpaca = text.find('ALPACA REAL-TIME EQUITY')
start = text.rfind('<div', 0, idx_alpaca)
parent_start = text.rfind('<div class="', 0, start)
grand_start = text.rfind('<div class="', 0, parent_start)

print("ALPACA Context:")
print(re.sub(r'[^\x00-\x7F]+', ' ', text[grand_start:idx_alpaca+100]))
