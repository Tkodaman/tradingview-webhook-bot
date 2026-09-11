with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    js = f.read()

def check_braces(code):
    stack = []
    in_string = False
    string_char = ''
    in_line_comment = False
    in_block_comment = False
    in_regex = False
    i = 0
    line_num = 1
    
    while i < len(code):
        c = code[i]
        nc = code[i+1] if i+1 < len(code) else ''
        
        if c == '\n':
            line_num += 1
            if in_line_comment:
                in_line_comment = False
                
        if in_line_comment:
            i += 1
            continue
            
        if in_block_comment:
            if c == '*' and nc == '/':
                in_block_comment = False
                i += 1
            i += 1
            continue
            
        if in_string:
            if c == '\\':
                i += 2
                continue
            if c == string_char:
                # Basic string end
                in_string = False
            elif string_char == '`' and c == '$' and nc == '{':
                # String interpolation start! We enter code mode!
                stack.append(('${', line_num))
                in_string = False
                i += 1
            i += 1
            continue
            
        # We are in CODE mode
        if c == '/' and nc == '/' and not in_regex:
            in_line_comment = True
            i += 1
            i += 1
            continue
            
        if c == '/' and nc == '*' and not in_regex:
            in_block_comment = True
            i += 1
            i += 1
            continue
            
        if c in ["'", '"', '`'] and not in_regex:
            in_string = True
            string_char = c
            i += 1
            continue
            
        if c in ['{', '(', '[']:
            stack.append((c, line_num))
        elif c in ['}', ')', ']']:
            if not stack:
                print(f"EXTRA {c} at line {line_num}")
            else:
                last_char, last_line = stack.pop()
                if c == '}' and last_char == '${':
                    # We resume the template literal!
                    in_string = True
                    string_char = '`'
                elif (last_char == '{' and c != '}') or \
                     (last_char == '(' and c != ')') or \
                     (last_char == '[' and c != ']'):
                    print(f"MISMATCH at line {line_num}: Expected match for {last_char} from {last_line}, got {c}")
                    
        i += 1
        
    for item in stack:
        print(f"UNCLOSED: {item}")

check_braces(js)
