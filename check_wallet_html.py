with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()
import re
idx = text.find('class="wallet-bar"')
print(text[max(0, idx-50):idx+400])
