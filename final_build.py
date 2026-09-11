from bs4 import BeautifulSoup
import re

with open('templates/cand_perfect_fixed.html', 'r', encoding='utf-8') as f:
    html_text = f.read()

# Wait, BeautifulSoup might choke on the garbage text or re-encode things.
# I'll just use regex.

# 1. Clean garbage from style tag
style_start = html_text.find('<style>')
style_end = html_text.find('</style>')
if style_start != -1 and style_end != -1:
    style_content = html_text[style_start:style_end]
    # Remove from <EPHEMERAL_MESSAGE> to </EPHEMERAL_MESSAGE>
    style_content = re.sub(r'<EPHEMERAL_MESSAGE>.*?</EPHEMERAL_MESSAGE>', '', style_content, flags=re.DOTALL)
    # Remove from "The following is an <EPHEMERAL_MESSAGE>" to </EPHEMERAL_MESSAGE>
    style_content = re.sub(r'The following is an <EPHEMERAL_MESSAGE>.*?</EPHEMERAL_MESSAGE>', '', style_content, flags=re.DOTALL)
    # Also there might be stray text like "tradingview-webhook-bot/templates/dashboard.html"
    style_content = re.sub(r',\"toolSummary\":\"[^\"]*\"\}\]\}', '', style_content)
    style_content = style_content.replace('tradingview-webhook-bot/templates/dashboard.html', '')
    style_content = re.sub(r'd At: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}', '', style_content)
    style_content = style_content.replace('No results found', '')
    style_content = style_content.replace('Total occurrences: 4', '')
    
    html_text = html_text[:style_start] + style_content + html_text[style_end:]

# 2. Keep the HTML layout exactly as is, but remove everything from the FIRST <script inside body to the end.
body_idx = html_text.find('<body>')
script_idx = html_text.find('<script', body_idx)

pure_html = html_text[:script_idx]

# 3. Read pure JS
with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    js = f.read()

final_html = pure_html + "\n<script>\n" + js + "\n</script>\n</body>\n</html>"

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(final_html)

print("Dashboard finalized properly! Size:", len(final_html))
