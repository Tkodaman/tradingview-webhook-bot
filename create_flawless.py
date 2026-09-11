import re

with open('templates/dashboard_final.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Remove ephemeral messages
text = re.sub(r'<EPHEMERAL_MESSAGE>.*?</EPHEMERAL_MESSAGE>', '', text, flags=re.DOTALL)
text = re.sub(r'The following is an <EPHEMERAL_MESSAGE>.*?</EPHEMERAL_MESSAGE>', '', text, flags=re.DOTALL)

# Find the LAST script tag start to separate HTML from JS
script_starts = [m.start() for m in re.finditer(r'<script>', text)]
if len(script_starts) > 0:
    last_script_start = script_starts[-1]
    html_part = text[:last_script_start]
else:
    html_part = text

# Ensure we remove any markdown garbage at the end
html_part = re.sub(r'`.*?\n', '', html_part)

# Read the clean JS
with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    js_part = f.read()

# Apply the flex order to fix the Aktif / Top 15 visual layout
idx_top15 = html_part.find('Top 15 Al')
if idx_top15 != -1:
    top15_start = html_part.rfind('<div style="background:linear-gradient', 0, idx_top15)
    if top15_start != -1:
        html_part = html_part[:top15_start] + html_part[top15_start:].replace('<div style="background:linear-gradient', '<div style="order:2; background:linear-gradient', 1)

idx_aktif = html_part.find('Aktif A')
if idx_aktif != -1:
    aktif_start = html_part.rfind('<div class="panel-container"', 0, idx_aktif)
    if aktif_start != -1:
        html_part = html_part[:aktif_start] + html_part[aktif_start:].replace('<div class="panel-container"', '<div class="panel-container" style="order:1;"', 1)

# Write final
final_content = html_part + "<script>\n" + js_part + "\n</script>\n</body>\n</html>"
with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(final_content)

print(f"Created flawless dashboard from dashboard_final.html. Size: {len(final_content)}")
