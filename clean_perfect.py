import re

with open('templates/cand_5b4e9_fixed.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Split into lines
lines = text.split('\n')
clean_lines = []
skip_mode = False

for line in lines:
    # Check for junk messages
    if '{"step_index":' in line or 'CRITICAL INSTRUCTION' in line or 'The above content does NOT show' in line or 'The following is an <EPHEMERAL_MESSAGE>' in line or '</EPHEMERAL_MESSAGE>' in line or '<planning_mode>' in line or '</planning_mode>' in line or '<bash_command_reminder>' in line or '</bash_command_reminder>' in line or '{"args"' in line:
        continue
    if '{"step_index":' in line:
        continue
    
    # Strip line numbers like "123: "
    match = re.match(r'^(\d+):\s(.*)', line)
    if match:
        line = match.group(2)
        
    clean_lines.append(line)

clean_text = '\n'.join(clean_lines)

# One more pass to remove any weird block JSON
# Often the ephemeral message is multi-line
clean_text = re.sub(r'\{"step_index":.*?\}', '', clean_text, flags=re.DOTALL)

with open('templates/cand_perfect.html', 'w', encoding='utf-8') as f:
    f.write(clean_text)

print(f"Cleaned cand_5b4e9. Length is {len(clean_text)}")
