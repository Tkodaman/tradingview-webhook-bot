with open('templates/cand_perfect2.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find("You're in planning mode. Exercise judgement")
print("Index of planning mode message:", idx)
