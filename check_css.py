with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
css_matches = re.findall(r'\.([^\{]*)\{([^\}]*)\}', text)
for cls, content in css_matches:
    if 'overflow' in content or 'height' in content or 'grid' in cls.lower() or 'log' in cls.lower():
        print(f"Class: {cls.strip()} -> {content.strip()}")
