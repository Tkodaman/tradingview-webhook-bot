with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
# Print terminals structure
t_matches = re.finditer(r'Terminali', text)
for m in t_matches:
    start = max(0, m.start() - 150)
    context = re.sub(r'[^\x00-\x7F]+', ' ', text[start:m.start()+50])
    print(f"Terminal context: {context}")
    
# Check for log-container or similar
log_matches = re.finditer(r'class="log-', text)
for m in log_matches:
    print(text[m.start()-20:m.start()+50])
    break
