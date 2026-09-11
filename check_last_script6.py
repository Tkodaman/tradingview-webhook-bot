import sys

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

sys.stdout.buffer.write(text[-500:].encode('utf-8'))
