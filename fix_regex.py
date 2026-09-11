with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    js = f.read()

import re
js = re.sub(r'chartEquity\.innerText\s*=\s*\$;', 'chartEquity.innerText = ${lastAlpacaBalance.toFixed(2)};', js)
js = re.sub(r'ce\.innerText\s*=\s*\$;', 'ce.innerText = ${lastAlpacaBalance.toFixed(2)};', js)

with open('pure_js_clean.js', 'w', encoding='utf-8') as f:
    f.write(js)

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

idx_first_script = html.rfind('<script>')
idx_last_script = html.rfind('</script>')
if idx_first_script != -1 and idx_last_script != -1:
    html = html[:idx_first_script+8] + '\n' + js + '\n' + html[idx_last_script:]
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Fixed JS syntax error in dashboard.html via regex!")
