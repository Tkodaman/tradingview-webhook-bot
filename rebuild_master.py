import re

with open('templates/cand_perfect_fixed.html', 'r', encoding='utf-8', errors='ignore') as f:
    cand_html = f.read()

# Extract top modern UI (from <body> up to the end of the KPI cards)
idx_body = cand_html.find('<body>')
idx_kpi_end = cand_html.find('<!-- ACTIVE POSITIONS TABLE (ENHANCED) -->')
top_modern_ui = cand_html[idx_body:idx_kpi_end]

# Now, we need the "Top 15 Momentum" HTML (I'll generate it below)
top_15_html = '''
    <div id="top5OpportunitiesWrap" style="background: var(--panel-bg); border: 1px solid var(--border-color); border-radius: 6px; margin: 10px 14px 20px 14px; padding: 12px;">
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
            <span style="font-size:14px;font-weight:700;color:#facc15;">🔥 Top 15 Alım Isı Haritası & Momentum (Canlı Fiyatlar)</span>
        </div>
        <div style="display:flex; gap:12px; align-items:flex-start;">
            <!-- Kripto -->
            <div style="flex:1; border: 1px solid rgba(255,255,255,0.05); border-radius:6px; padding:8px;">
                <div style="font-size:12px; font-weight:bold; margin-bottom:8px; color:#4ade80; text-align:center;">🪙 Kripto Piyasası</div>
                <div id="top15CryptoBody" style="display:flex; flex-direction:column; gap:4px; font-size:11px;">
                    <!-- Data here -->
                </div>
            </div>
            <!-- Bist -->
            <div style="flex:1; border: 1px solid rgba(255,255,255,0.05); border-radius:6px; padding:8px;">
                <div style="font-size:12px; font-weight:bold; margin-bottom:8px; color:#38bdf8; text-align:center;">🇹🇷 BIST 100/30</div>
                <div id="top15BistBody" style="display:flex; flex-direction:column; gap:4px; font-size:11px;">
                    <!-- Data here -->
                </div>
            </div>
            <!-- Nasdaq -->
            <div style="flex:1; border: 1px solid rgba(255,255,255,0.05); border-radius:6px; padding:8px;">
                <div style="font-size:12px; font-weight:bold; margin-bottom:8px; color:#f472b6; text-align:center;">🇺🇸 NASDAQ Mega-Cap</div>
                <div id="top15NasdaqBody" style="display:flex; flex-direction:column; gap:4px; font-size:11px;">
                    <!-- Data here -->
                </div>
            </div>
        </div>
    </div>
'''

# Now extract the bottom HTML from dashboard_working_backup.html
with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8', errors='ignore') as f:
    working = f.read()

# I want the 3-MARKET SEPARATED WINDOWS and downwards
idx_markets = working.find('<!-- ========================================================================= -->\n    <!-- 3-MARKET SEPARATED')
idx_scripts = working.find('<script>')
bottom_html = working[idx_markets:idx_scripts]

# Also extract the Modals
idx_modals = working.find('<!-- MODALS')
if idx_modals != -1 and idx_modals < idx_scripts:
    bottom_html = working[idx_markets:idx_modals] + working[idx_modals:idx_scripts]

# Wait, what about the Active Positions Table?
idx_active_pos = working.find('<!-- ACTIVE POSITIONS TABLE -->')
idx_markets_container = working.find('<!-- ========================================================================= -->', idx_active_pos)
active_pos_html = working[idx_active_pos:idx_markets_container]

# Read the clean JS
with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    js = f.read()

# Build the final file
final_html = top_modern_ui + top_15_html + active_pos_html + bottom_html + "\n<script>\n" + js + "\n</script>\n</body>\n</html>"

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(final_html)

print("SUCCESS: Wrote dashboard.html, size:", len(final_html))
