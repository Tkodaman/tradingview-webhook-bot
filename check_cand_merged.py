with open('templates/cand_merged.html', 'r', encoding='utf-8') as f:
    text = f.read()

print("cand_merged size:", len(text))
print("Has EPHEMERAL_MESSAGE:", "EPHEMERAL_MESSAGE" in text)
