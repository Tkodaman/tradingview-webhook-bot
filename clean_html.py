import re

def clean_html(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    
    lines = text.split('\n')
    cleaned_lines = []
    for line in lines:
        # Match "123: " at the beginning of the line
        m = re.match(r'^\d+:\s(.*)', line)
        if m:
            cleaned_lines.append(m.group(1))
        else:
            cleaned_lines.append(line)
            
    with open(filepath + '_clean.html', 'w', encoding='utf-8') as f:
        f.write('\n'.join(cleaned_lines))

clean_html(r'templates\cand_22e24.html')
