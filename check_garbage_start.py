with open('templates/dashboard_clean.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('overflow-x: auto;')
import sys
sys.stdout.buffer.write(text[idx:idx+1500].encode('utf-8'))
