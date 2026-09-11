with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# find Seans Saati
idx = text.find('Seans Saati & Countdown')
idx_start = text.rfind('<div class="panel"', 0, idx)

# now print the next 2000 chars from idx_start
print(text[idx_start:idx_start+2000].encode('ascii', 'ignore').decode('ascii'))
