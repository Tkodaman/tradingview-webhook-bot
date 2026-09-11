with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
matches = re.findall(r'<div[^>]*class="[^"]*market-window[^"]*"[^>]*>[\s\S]*?</style>', text)
print("Found market-window:", text.find('market-window'))
