with open('templates/dashboard_fixed.html', 'r', encoding='utf-8') as f:
    text = f.read()

print("dashboard_fixed size:", len(text))
import re
matches = re.findall(r'<div class="panel-header-title">.*?</div>', text, flags=re.DOTALL)
for i, m in enumerate(matches):
    clean = re.sub(r'[^\x00-\x7F]+', ' ', m)
    print(f"Panel {i+1}: {clean.replace(chr(10), ' ').strip()[:100]}")
