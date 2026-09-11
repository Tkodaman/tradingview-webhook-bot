import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Find the first <script
idx = html.find('<script')
if idx != -1:
    html = html[:idx]

final_html = html + "\n<script>\n" + js + "\n</script>\n</body>\n</html>"

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(final_html)

print("Dashboard finalized! Total size:", len(final_html))
