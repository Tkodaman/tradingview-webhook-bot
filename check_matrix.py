with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
fetch_matrix = re.search(r'async function updateLiveMatrix\(\)\s*\{.*?\}', text, re.DOTALL)
if fetch_matrix:
    print("Found updateLiveMatrix!")
    print(fetch_matrix.group(0)[:500])
else:
    print("NO updateLiveMatrix FOUND!")
