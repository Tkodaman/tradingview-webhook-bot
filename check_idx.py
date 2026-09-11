with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    text = f.read()

start = max(0, 45281 - 100)
import sys
sys.stdout.buffer.write(text[start:start+500].encode('utf-8'))
