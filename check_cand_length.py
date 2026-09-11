with open('templates/cand_perfect2.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('The following is an <EPHEMERAL_MESSAGE>')
print("Index of Ephemeral message:", idx)
print("Length of file:", len(text))
