with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import sys
sys.stdout.buffer.write(text[-2000:].encode('utf-8'))
