with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    js = f.read()

import re
stack = []
line_no = 1
in_string = False
string_char = ''
escape = False
in_comment = False
in_block_comment = False
i = 0

while i < len(js):
    char = js[i]
    next_char = js[i+1] if i+1 < len(js) else ''
    
    if char == '\n':
        line_no += 1
        in_comment = False

    if not in_string and not in_comment and not in_block_comment:
        if char == '/' and next_char == '/':
            in_comment = True
            i += 1
        elif char == '/' and next_char == '*':
            in_block_comment = True
            i += 1
        elif char in ["'", '"', '']:
            in_string = True
            string_char = char
        elif char in ['{', '(', '[']:
            stack.append((char, line_no))
        elif char in ['}', ')', ']']:
            if not stack:
                pass
            else:
                last_char, last_line = stack.pop()
                if (last_char == '{' and char != '}') or \
                   (last_char == '(' and char != ')') or \
                   (last_char == '[' and char != ']'):
                    print(f"MISMATCH at line {line_no}. Expected match for {last_char} from {last_line}, got {char}")
                    break
    elif in_block_comment:
        if char == '*' and next_char == '/':
            in_block_comment = False
            i += 1
    elif in_string:
        if escape:
            escape = False
        elif char == '\\':
            escape = True
        elif char == string_char:
            in_string = False
            
    i += 1

