with open('templates/cand_perfect2.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
ws_match = re.search(r'const wsUrl =.*?};', text, re.DOTALL)
if ws_match:
    print("Has WS")
else:
    print("Does NOT have WS")
    
# Let's insert the WS logic from dashboard.html!
with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    dash = f.read()
dash_ws = re.search(r'(const wsUrl =.*?ws\.onclose =.*?\n\s*};)', dash, re.DOTALL)

if not ws_match and dash_ws:
    # insert dash_ws.group(1) into cand_perfect2 before '// LLM blink animation' or just at the end of scripts.
    text = text.replace('// LLM blink animation', dash_ws.group(1) + '\n\n// LLM blink animation')
    # and fix the missing scripts issue again just in case
    text = text.replace('window.onerror =', '<script>\nwindow.onerror =', 1)
    
    # Fix the syntax error (missing string interpolation)
    text = re.sub(r'\$\$\{', '${', text)
    text = re.sub(r'toFixed\(2\)\};', 'toFixed(2)};', text)

    with open('templates/cand_merged.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Saved cand_merged.html with WS!")
