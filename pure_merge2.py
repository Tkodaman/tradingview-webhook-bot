import re

with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8') as f:
    working = f.read()

with open('templates/cand_perfect_clean.html', 'r', encoding='utf-8') as f:
    dash = f.read()

working_css = re.search(r'<style>(.*?)</style>', working, re.DOTALL).group(1)
merged_css = working_css

idx_body_start_dash = dash.find('<div class="header-section">')
if idx_body_start_dash == -1: idx_body_start_dash = dash.find('<body')
idx_body_end_dash = dash.rfind('<script')
if idx_body_end_dash == -1: idx_body_end_dash = dash.rfind('</body>')
top_html = dash[idx_body_start_dash:idx_body_end_dash]

idx_active_start = working.find('<div class="panel">', 29000)
idx_active_end = working.find('<script>', idx_active_start)
bottom_html = working[idx_active_start:idx_active_end]

working_js = re.search(r'<script>(.*?)</script>\s*</body>', working, re.DOTALL)
if not working_js:
    working_js = re.search(r'<script>(.*?)</script>', working[idx_active_end:], re.DOTALL)
working_js_code = working_js.group(1) if working_js else ""

top_html = top_html.replace('id="gridCrypto"', 'id="windowCrypto"')
top_html = top_html.replace('id="gridBist"', 'id="windowBist"')
top_html = top_html.replace('id="gridNasdaq"', 'id="windowNasdaq"')

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
{working_js_code}
</script>
</body>
</html>'''

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(final_html)

print("Merged perfectly without corrupted JS!")
