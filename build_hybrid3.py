import re

with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    dash = f.read()

# Extract ws logic using regex
match = re.search(r'(const wsUrl =.*?ws\.onclose =.*?\n\s*};)', dash, re.DOTALL)
if match:
    ws_block = match.group(1)
    print("Found ws block length:", len(ws_block))
    
    with open('templates/cand_5b4e9.html', 'r', encoding='utf-8', errors='ignore') as f:
        cand = f.read()

    # ensure <script> tags are correct
    cand = cand.replace('window.onerror =', '<script>\nwindow.onerror =', 1)
    # The ending script tag is already there: it has 3 </script> and 1 <script>. 
    # But wait, cand_5b4e9.html line 4 had <script>
    # So if it HAS <script>, why did check_cand_js_tags say 1 script?
    # Because there WAS a script at line 4! But what about the massive body?
    # Actually I'll just find // LLM blink animation and insert ws_block before it!
    cand = cand.replace('// LLM blink animation', ws_block + '\n\n// LLM blink animation')
    
    with open('templates/dashboard_hybrid.html', 'w', encoding='utf-8') as f:
        f.write(cand)
    print("Saved hybrid!")
else:
    print("Could not find ws block using regex")
