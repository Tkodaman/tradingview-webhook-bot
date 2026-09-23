import re

with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8') as f:
    working = f.read()

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    dash = f.read()

# 1. Extract CSS
# dashboard.html has the new CSS for the 3-groups, but might be missing CSS for the bottom half.
# working_backup has CSS for the bottom half.
# Let's combine them: Working CSS first, then dashboard CSS (to override).
working_css = re.search(r'<style>(.*?)</style>', working, re.DOTALL).group(1)
dash_css = re.search(r'<style>(.*?)</style>', dash, re.DOTALL).group(1)
merged_css = working_css + "\n/* --- NEW CSS --- */\n" + dash_css

# 2. Extract HTML body (top half) from dashboard.html
# dashboard.html has <div class="header-section"> ... up to right before <script>
idx_body_start_dash = dash.find('<div class="header-section">')
if idx_body_start_dash == -1: idx_body_start_dash = dash.find('<body')
idx_body_end_dash = dash.rfind('<script', 0, dash.rfind('<script>'))
if idx_body_end_dash == -1: idx_body_end_dash = dash.rfind('<script>')
top_html = dash[idx_body_start_dash:idx_body_end_dash]

# 3. Extract HTML body (bottom half) from working_backup
# The bottom half starts with <div class="panel"> (Aktif Acik Pozisyonlar)
idx_active_start = working.find('<div class="panel">', 29000)
idx_active_end = working.find('<script>', idx_active_start)
bottom_html = working[idx_active_start:idx_active_end]

# 4. Combine JS
# working_backup has all the WebSocket, fetchLiveMatrix, active positions logic.
# dashboard.html has the new fetchTop5Momentum, fetchMacroData, etc.
working_js = re.search(r'<script>(.*?)</script>\s*</body>', working, re.DOTALL)
if not working_js:
    working_js = re.search(r'<script>(.*?)</script>', working[idx_active_end:], re.DOTALL)
working_js_code = working_js.group(1) if working_js else ""

dash_js = re.search(r'<script>(.*?)</script>\s*</body>', dash, re.DOTALL)
if not dash_js:
    # search the last script tag
    scripts = re.findall(r'<script>(.*?)</script>', dash, re.DOTALL)
    dash_js_code = scripts[-1] if scripts else ""
else:
    dash_js_code = dash_js.group(1)

merged_js = working_js_code + "\n// --- NEW JS --- \n" + dash_js_code

# Assemble final HTML
final_html = f'''<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TradingView AI Webhook Gateway & Otonom Piyasa Kokpiti</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
{merged_css}
    </style>
</head>
<body>
{top_html}
{bottom_html}
<script>
{merged_js}
</script>
</body>
</html>'''

# Let's fix up some layout stuff if necessary (e.g. putting it all in the same container).
# The top_html might have an unclosed container if it was truncated!
# Let's check div balance
def balance_divs(html):
    opens = html.count('<div')
    closes = html.count('</div')
    if opens > closes:
        return html + '</div>' * (opens - closes)
    return html

top_html = balance_divs(top_html)
bottom_html = balance_divs(bottom_html)

# We'll re-assemble it to make sure the tags match.
final_html = f'''<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TradingView AI Webhook Gateway & Otonom Piyasa Kokpiti</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
{merged_css}
    </style>
</head>
<body>
{top_html}
{bottom_html}
<script>
{merged_js}
</script>
</body>
</html>'''

with open('templates/dashboard_final.html', 'w', encoding='utf-8') as f:
    f.write(final_html)

print("Merge complete! Length:", len(final_html))
