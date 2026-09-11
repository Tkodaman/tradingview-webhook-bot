with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re

# Extract all script tags
scripts = re.findall(r'<script>(.*?)</script>', html, flags=re.DOTALL)

for i, js in enumerate(scripts):
    stack = []
    line_no = 1
    in_string = False
    string_char = ''
    escape = False
    
    for char in js:
        if char == '\n':
            line_no += 1
            
        if not in_string:
            if char in ["'", '"', '']:
                in_string = True
                string_char = char
            elif char in ['{', '(', '[']:
                stack.append((char, line_no))
            elif char in ['}', ')', ']']:
                if not stack:
                    print(f"Script {i}: EXTRA {char} at line {line_no}")
                else:
                    last_char, last_line = stack.pop()
                    if (last_char == '{' and char != '}') or \
                       (last_char == '(' and char != ')') or \
                       (last_char == '[' and char != ']'):
                        print(f"Script {i}: MISMATCH at line {line_no}. Expected match for {last_char} from {last_line}, got {char}")
        else:
            if escape:
                escape = False
            elif char == '\\':
                escape = True
            elif char == string_char:
                in_string = False

    if stack:
        print(f"Script {i}: UNCLOSED {stack}")
    else:
        print(f"Script {i}: Braces OK!")

