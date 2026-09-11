import glob

files = glob.glob('templates/cand_*.html')
for f in files:
    with open(f, 'r', encoding='utf-8', errors='ignore') as file:
        text = file.read()
        if 'market-window-crypto' in text:
            if '{"step_index"' not in text and 'TRUNCATED' not in text.upper():
                print(f"CLEAN AND HAS CRYPTO: {f} (Length: {len(text)})")
