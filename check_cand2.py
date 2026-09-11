with open('templates/cand_perfect2.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx_script = text.find('<script>')
print(text[idx_script-1000:idx_script].encode('ascii', 'ignore').decode('ascii'))
