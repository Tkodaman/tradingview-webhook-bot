with open('templates/dashboard_final.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# 1. Extract Top HTML from dashboard_final.html (up to the end of Risk Parametreleri panel)
idx_body = text.find('<body>')
idx_garbage = text.find("You're in planning mode. Exercise judgement")
idx_risk = text.find('Risk Parametreleri', idx_garbage if idx_garbage != -1 else 0)
# Find the end of the Risk Parametreleri panel
idx_risk_end = text.find('</div>\n        </div>', idx_risk)
if idx_risk_end == -1: idx_risk_end = text.find('</div>\r\n        </div>', idx_risk)
if idx_risk_end == -1: idx_risk_end = text.find('</div>        </div>', idx_risk)

# Add some buffer to ensure we close the 3-column grid
top_html = text[idx_body:idx_risk_end+20]

# Now REPLACE the garbage in top_html
idx_garb = top_html.find("You're in planning mode. Exercise judgement")
if idx_garb != -1:
    idx_start = top_html.rfind('<div class="panel"', 0, idx_garb)
    idx_end = top_html.rfind('<div class="panel"', idx_garb, top_html.find('Risk Parametreleri'))
    replacement = '''<div class="panel" style="padding:16px;">
            <div class="panel-header" style="margin-bottom:12px;">
                <div class="panel-header-title"><span>📊</span> Portföy Dağılımı</div>
            </div>
            
            <div style="display:flex; flex-direction:column; gap:12px;">
                <div>
                    <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px;">
                        <span style="color:#d8b4fe; font-weight:600;">Kripto (Binance)</span>
                        <span id="distCryptoPct" style="color:#fff; font-family:'JetBrains Mono';">0.0%</span>
                    </div>
                    <div style="width:100%; background:rgba(168,85,247,0.1); height:8px; border-radius:4px; overflow:hidden;">
                        <div id="distCryptoBar" style="width:0%; background:linear-gradient(90deg, #9333ea, #d8b4fe); height:100%; border-radius:4px; transition: width 0.5s;"></div>
                    </div>
                </div>
                <div>
                    <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px;">
                        <span style="color:#86efac; font-weight:600;">BIST 100</span>
                        <span id="distBistPct" style="color:#fff; font-family:'JetBrains Mono';">0.0%</span>
                    </div>
                    <div style="width:100%; background:rgba(74,222,128,0.1); height:8px; border-radius:4px; overflow:hidden;">
                        <div id="distBistBar" style="width:0%; background:linear-gradient(90deg, #16a34a, #4ade80); height:100%; border-radius:4px; transition: width 0.5s;"></div>
                    </div>
                </div>
                <div>
                    <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px;">
                        <span style="color:#93c5fd; font-weight:600;">NASDAQ</span>
                        <span id="distNasdaqPct" style="color:#fff; font-family:'JetBrains Mono';">0.0%</span>
                    </div>
                    <div style="width:100%; background:rgba(59,130,246,0.1); height:8px; border-radius:4px; overflow:hidden;">
                        <div id="distNasdaqBar" style="width:0%; background:linear-gradient(90deg, #2563eb, #60a5fa); height:100%; border-radius:4px; transition: width 0.5s;"></div>
                    </div>
                </div>
                <div>
                    <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px;">
                        <span style="color:#cbd5e1; font-weight:600;">Nakit (Rezerv)</span>
                        <span id="distCashPct" style="color:#fff; font-family:'JetBrains Mono';">100.0%</span>
                    </div>
                    <div style="width:100%; background:rgba(203,213,225,0.1); height:8px; border-radius:4px; overflow:hidden;">
                        <div id="distCashBar" style="width:100%; background:linear-gradient(90deg, #64748b, #cbd5e1); height:100%; border-radius:4px; transition: width 0.5s;"></div>
                    </div>
                </div>
                <div style="display:flex; justify-content:space-between; font-size:10px; color:rgba(255,255,255,0.4); margin-top:4px;">
                    <span>Aktif Pozisyonlar Bazlı Tahmini</span>
                </div>
            </div>
        </div>\n'''
    top_html = top_html[:idx_start] + replacement + top_html[idx_end:]


# 2. Extract Bottom HTML from dashboard_working_backup.html (The 3 market grids + the rest of the panels)
with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8', errors='ignore') as f:
    working = f.read()

# We need the active positions panel, the 3 market grids, and the history table.
# Let's find "Aktif Ak Pozisyonlar" in working
idx_aktif = working.find('Aktif')
idx_bottom_start = working.rfind('<div class="panel"', 0, idx_aktif)
idx_script = working.find('<script>', idx_bottom_start)
bottom_html = working[idx_bottom_start:idx_script]

# Change gridCrypto to windowCrypto in bottom_html to match the JS!
bottom_html = bottom_html.replace('id="gridCrypto"', 'id="windowCrypto"')
bottom_html = bottom_html.replace('id="gridBist"', 'id="windowBist"')
bottom_html = bottom_html.replace('id="gridNasdaq"', 'id="windowNasdaq"')

# 3. Extract CSS and JS from dashboard_working_backup.html
import re
working_css = re.search(r'<style>(.*?)</style>', working, re.DOTALL).group(1)
idx_w_first_script = working.find('<script>', working.find('<body>'))
idx_w_script_end = working.rfind('</script>')
working_js_code = working[idx_w_first_script+8:idx_w_script_end]

# FIX the Islem syntax error in working_js_code
working_js_code = re.sub(r"return idx === 0 \? 'Start' : .*?;", "return idx === 0 ? 'Start' : 'Islem #' + idx;", working_js_code)

final_html = f'''<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>TradingView AI Webhook Gateway & Otonom Piyasa Kokpiti</title>
    <link href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
{working_css}
    </style>
</head>
{top_html}

{bottom_html}

<script>
{working_js_code}
</script>
</body>
</html>'''

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(final_html)

print("ULTIMATE MERGE COMPLETED.")
