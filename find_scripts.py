import re
with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8') as f:
    text = f.read()

# find script tag contents
scripts = re.findall(r'<script>(.*?)</script>', text, re.DOTALL)
for i, script in enumerate(scripts):
    if 'wsUrl' in script or 'fetch' in script:
        print(f"Script {i} snippet:")
        print(script[:300])
