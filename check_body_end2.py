import sys

with open('final_clean_html_body.txt', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

sys.stdout.buffer.write(text[-1500:].encode('utf-8'))
