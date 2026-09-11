with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8') as f:
    text = f.read()
    
import re
# Find anything that mentions "active" or "history" in JS
matches = re.findall(r'function \w+\(.*?\)', text[text.find('<script>'):])
print("Functions found:", set(matches))
