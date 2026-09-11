with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
css_matches = re.findall(r'\.([^\{]*)\{([^\}]*)\}', text)
for cls, content in css_matches:
    cls = cls.strip()
    if 'width:' in content or 'max-width:' in content:
        if 'body' in cls or 'container' in cls or 'panel' in cls or 'content' in cls:
            print(f"Class: {cls} -> {content.strip()}")
