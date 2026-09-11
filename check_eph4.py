import sys

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('EPHEMERAL_MESSAGE')
if idx != -1:
    sys.stdout.buffer.write(text[max(0, idx-100):idx+50].encode('utf-8'))
else:
    print("NOT FOUND")
