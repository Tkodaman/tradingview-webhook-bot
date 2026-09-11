with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
print("Has 15 Momentum:", "15 Momentum" in text)
print("Has Aktif:", "Aktif Açık" in text or "Aktif A" in text)
print("Has Top 15:", "Top 15" in text)
