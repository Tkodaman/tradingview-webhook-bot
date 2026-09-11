import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# The second wsUrl comes after "// --- NEW JS --- "
idx = text.find('// --- NEW JS ---')
if idx != -1:
    # Just remove the whole duplicate const wsUrl ... block
    # It looks like:
    # const wsUrl = ws:///ws;
    # let ws = null;
    # ...
    # function connectWebSocket() { ... }
    # We can just use re.sub to remove the second connectWebSocket block completely
    # Or simpler: change 'const wsUrl' to 'var wsUrl2'
    
    tail = text[idx:]
    tail = tail.replace('const wsUrl =', '// const wsUrl =')
    tail = tail.replace('let ws = null;', '// let ws = null;')
    # also we should comment out the duplicate connectWebSocket function if it exists
    tail = re.sub(r'function connectWebSocket\(\)\s*\{.*?(?=// LLM blink animation)', '/* duplicate connectWebSocket removed */', tail, flags=re.DOTALL)
    
    text = text[:idx] + tail
    
with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Fixed duplicate variables!")
