with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()
import re
js = re.search(r'<script>(.*)</script>', text, re.DOTALL)
if js:
    code = js.group(1)
    print("Code length:", len(code))
    
    # Let's check for initialization blocks like 'DOMContentLoaded'
    dom_matches = re.findall(r'DOMContentLoaded', code)
    print("DOMContentLoaded matches:", len(dom_matches))
    # Check for setInterval calls not inside functions
    
    # Or maybe there's a syntax error like an unclosed bracket!
    opens = code.count('{')
    closes = code.count('}')
    print(f"Brackets: {opens} {closes}")
