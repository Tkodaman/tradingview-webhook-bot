with open('backup_html_structure.txt', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('.inner-box-title')
import sys
sys.stdout.buffer.write(text[idx:idx+500].encode('utf-8'))
