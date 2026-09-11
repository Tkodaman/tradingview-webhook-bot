import sys
with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    text = f.read()

sys.stdout.buffer.write(text[-200:].encode('utf-8'))
