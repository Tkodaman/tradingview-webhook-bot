with open('templates/cand_perfect_clean.html', 'r', encoding='utf-8') as f:
    text = f.read()

print("Size:", len(text))
print("Has Top 15:", "Top 15" in text)
