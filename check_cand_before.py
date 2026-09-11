with open('templates/cand_perfect2.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx_eph = text.find('The following is an <EPHEMERAL_MESSAGE>')
print(text[idx_eph-1000:idx_eph].encode('ascii', 'ignore').decode('ascii'))
