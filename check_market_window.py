with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()
import re
matches = re.search(r'\.market-window\s*\{([^\}]*)\}', text)
if matches:
    print(".market-window:", matches.group(1).strip())
