with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

import re
script_idx = html.find('<script>')
if script_idx != -1:
    pure_html = html[:script_idx]
    
    with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
        js = f.read()

    final_html = pure_html + "<script>\n" + js + "\n</script>\n</body>\n</html>"

    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(final_html)
    print("Re-injected clean JS into dashboard.html")
else:
    print("Could not find <script> in dashboard.html")
