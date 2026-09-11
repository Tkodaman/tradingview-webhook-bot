with open('templates/cand_perfect2.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

if "Top 15" in text:
    print("Top 15 found in cand_perfect2.html")
