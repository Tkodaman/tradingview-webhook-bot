with open('templates/cand_perfect2.html', 'r', encoding='utf-8') as f:
    text = f.read()

print("cand_perfect2 has fetchLiveMatrix:", 'fetchLiveMatrix' in text)
