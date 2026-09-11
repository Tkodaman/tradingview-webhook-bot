with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
fetch_matrix = re.search(r'async function.*?\n.*?fetch\(''/api/market/live-matrix''\).*?\}', text, re.DOTALL)
if fetch_matrix:
    print("Found matrix fetch function!")
    print(fetch_matrix.group(0)[:500])
else:
    # Just grab the block around it
    idx = text.find('/api/market/live-matrix')
    if idx != -1:
        start = max(0, idx - 200)
        end = min(len(text), idx + 800)
        print("Found occurrence:")
        print(text[start:end])
