import re
import os

with open('templates/cand_merged.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# 1. Remove all <EPHEMERAL_MESSAGE> blocks
text = re.sub(r'<EPHEMERAL_MESSAGE>.*?</EPHEMERAL_MESSAGE>', '', text, flags=re.DOTALL)
text = re.sub(r'The following is an <EPHEMERAL_MESSAGE>.*?</EPHEMERAL_MESSAGE>', '', text, flags=re.DOTALL)

# 2. Extract HTML up to the first <script> inside the body, OR up to the bottom script if there are multiple
# The easiest way: find the start of the LAST script tag, which is the main JS.
# cand_merged.html might have Chart.js in the head, and main JS at the bottom.
script_starts = [m.start() for m in re.finditer(r'<script>', text)]
if len(script_starts) > 0:
    last_script_start = script_starts[-1]
    html_part = text[:last_script_start]
else:
    html_part = text

# Ensure we remove any lingering garbage
html_part = re.sub(r'`.*?\n', '', html_part)

# 3. Read the syntax-error-free JS
with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    js_part = f.read()

# 4. Swap Top 15 and Aktif in html_part
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

# 5. Combine and save
final_content = html_part + "<script>\n" + js_part + "\n</script>\n</body>\n</html>"

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(final_content)

print(f"Reconstructed perfect dashboard. Size: {len(final_content)}")
