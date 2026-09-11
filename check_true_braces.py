import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

scripts = re.findall(r'<script>(.*?)</script>', html, flags=re.DOTALL)
js = scripts[1]

# Remove all string literals
# This is tricky with regex, let's use a simple state machine

def strip_js(js_code):
    out = []
    i = 0
    in_str = False
    str_char = ''
    in_line_comm = False
    in_block_comm = False
    
    while i < len(js_code):
        c = js_code[i]
        nc = js_code[i+1] if i+1 < len(js_code) else ''
        
        if in_str:
            if c == '\\':
                i += 2
                continue
            if c == str_char:
                in_str = False
            i += 1
            continue
            
        if in_line_comm:
            if c == '\n':
                in_line_comm = False
            i += 1
            continue
            
        if in_block_comm:
            if c == '*' and nc == '/':
                in_block_comm = False
                i += 2
                continue
            i += 1
            continue
            
        if c == '/' and nc == '/':
            in_line_comm = True
            i += 2
            continue
            
        if c == '/' and nc == '*':
            in_block_comm = True
            i += 2
            continue
            
        if c in ["'", '"', '']:
            in_str = True
            str_char = c
            i += 1
            continue
            
        out.append(c)
        i += 1
        
    return "".join(out)

clean_js = strip_js(js)

stack = []
lines = clean_js.split('\n')
for line_no, line in enumerate(lines):
    for char in line:
        if char == '{':
            stack.append((char, line_no + 1))
        elif char == '}':
            if not stack:
                print(f"EXTRA }} at line {line_no + 1}")
            else:
                stack.pop()

if stack:
    print("UNCLOSED BRACES:")
    for item in stack:
        print(item)
else:
    print("BRACES ARE PERFECTLY BALANCED!")

