with open('templates/cand_perfect_clean.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

print("File ends with:", repr(text[-200:]))
