with open('templates/cand_5b4e9.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# The junk starts at {"step_index": (idx 32948)
idx = text.find('{"step_index":')
if idx != -1:
    print("Found junk at", idx)
    # the text before this is pure CSS!
    print("CSS length before junk:", len(text[:idx]))
    print(text[idx-200:idx])
