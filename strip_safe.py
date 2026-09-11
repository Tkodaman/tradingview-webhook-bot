with open('templates/dashboard_final.html', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    s = line.strip()
    if s == '<EPHEMERAL_MESSAGE>':
        skip = True
        continue
    
    # If we hit an empty line or a valid HTML/JS line while skipping, maybe stop skipping?
    # No, the system message is multi-line.
    # The system message ends with CRITICAL INSTRUCTION 2: ...'.
    if skip and ("CRITICAL INSTRUCTION 2: ...'." in s or "</bash_command_reminder>" in s):
        skip = False
        continue
        
    if not skip:
        # Also remove any stray <truncated messages
        if '<truncated' not in s and 'NOTE: The output was truncated' not in s:
            new_lines.append(line)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("Safely stripped!")
