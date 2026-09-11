with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's find any setInterval or top-level function calls
import re
# Print the last 100 lines of the script
script_idx = text.rfind('<script>')
if script_idx != -1:
    lines = text[script_idx:].split('\n')
    for line in lines[-100:]:
        print(line)
