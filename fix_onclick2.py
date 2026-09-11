with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re
html = re.sub(r'(showToast\(\$\{item.symbol\} se[çc]ildi\.[^\n]+)\n\s*\} else \{', r'\1\n                    };\n                } else {', html)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Regex replace applied.")
