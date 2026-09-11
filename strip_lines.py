with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

new_lines = []
skip = False
for line in lines:
    if '<EPHEMERAL_MESSAGE>' in line or '<SYSTEM_MESSAGE>' in line or '<planning_mode>' in line or 'The following is an <EPHEMERAL_MESSAGE>' in line or '**The earlier parts' in line:
        skip = True
    
    if not skip:
        new_lines.append(line)
        
    if '</EPHEMERAL_MESSAGE>' in line or '</SYSTEM_MESSAGE>' in line or '</planning_mode>' in line or '</bash_command_reminder>' in line:
        skip = False

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("Stripped completely!")
