with open('templates/cand_perfect_fixed.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Find <body>
body_idx = html.find('<body>')
if body_idx == -1: body_idx = 0

# Find the first script inside body
script_idx = html.find('<script', body_idx)
if script_idx != -1:
    pure_html = html[:script_idx]
    
    with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
        js = f.read()

    final_html = pure_html + "\n<script>\n" + js + "\n</script>\n</body>\n</html>"

    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(final_html)

    print("Restored from cand_perfect_fixed.html! Size:", len(final_html))
else:
    print("Could not find script inside body")
