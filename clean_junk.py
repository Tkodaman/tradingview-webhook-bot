with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    lines = f.readlines()

in_junk = False
clean_lines = []
for i, line in enumerate(lines):
    if line.startswith('{"step_index":') or 'CRITICAL INSTRUCTION' in line or '{"args"' in line:
        in_junk = True
    
    if in_junk and (line.strip() == '        /* 2-COLUMN GRID (RULES & SUMMARY) */' or line.strip() == '        .inner-box {' or line.strip() == '        .stat-grid {'):
        in_junk = False
        
    if not in_junk:
        clean_lines.append(line)
        
with open('test_clean.html', 'w', encoding='utf-8') as f:
    f.writelines(clean_lines)

print("Removed junk. Original lines:", len(lines), "Clean lines:", len(clean_lines))
