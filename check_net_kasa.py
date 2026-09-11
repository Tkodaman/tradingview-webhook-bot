import sys

with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('NET KASA (EQUITY)')
start = max(0, idx - 400)
end = min(len(text), idx + 20)

sys.stdout.buffer.write(text[start:end].encode('utf-8'))
