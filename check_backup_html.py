with open('backup_html_structure.txt', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()
print("Contains Top 15:", "Top 15" in text)
print("Contains EPHEMERAL:", "EPHEMERAL" in text)
print("Size:", len(text))
