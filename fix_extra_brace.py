with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    lines = f.readlines()

if '};' in lines[196]:
    lines.pop(196)

with open('pure_js_clean.js', 'w', encoding='utf-8') as f:
    f.writelines(lines)

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

idx_first_script = html.rfind('<script>')
idx_last_script = html.rfind('</script>')
if idx_first_script != -1 and idx_last_script != -1:
    html = html[:idx_first_script+8] + '\n' + "".join(lines) + '\n' + html[idx_last_script:]
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Removed extra }; and rebuilt dashboard.html")
