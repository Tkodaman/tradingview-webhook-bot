with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
html = re.sub(r"(showToast\(\$\{item\.symbol\} se[çc]ildi\. Hızlı emir penceresi açıldı\., 'info'\);\r?\n\s*)\} else \{", r"\1};\n                } else {", text)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)

print("Regex replace applied with \r?")
