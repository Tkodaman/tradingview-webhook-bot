import re
with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8') as f:
    text = f.read()

# find where the old top section ends and the active positions panel begins
idx_active = text.find('<div class="panel">', 29000)

# the top section (Header, Slider, Risk Modes) is what the user already has.
# Actually, the user's FIRST screenshot shows the NEW header, the slider, the risk modes, AND THEN the 3 groups!
# So the user wants the exact layout they have right now, BUT with the bottom half and JS added!

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    dash = f.read()

# Where does dashboard.html end its body content?
idx_dash_script = dash.find('<script>', dash.find('<div class="action-buttons">'))
if idx_dash_script == -1:
    idx_dash_script = dash.find('</body>')

# Let's extract the JS from working_backup
js_start = text.find('<script>', idx_active)
js_content = text[js_start:text.find('</body>')]

print(f"JS start: {js_start}, Length of JS: {len(js_content)}")
