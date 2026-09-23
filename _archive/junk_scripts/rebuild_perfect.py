with open('templates/dashboard_final.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re

# 1. We replace the garbage inside the Portfoy panel
idx_garbage = text.find("You're in planning mode. Exercise judgement")
if idx_garbage != -1:
    idx_start = text.rfind('<div class="panel"', 0, idx_garbage)
    idx_risk = text.find('Risk Parametreleri', idx_garbage)
    idx_end = text.rfind('<div class="panel"', idx_garbage, idx_risk)
    
    replacement = '''<div class="panel" style="padding:16px;">
            <div class="panel-header" style="margin-bottom:12px;">
                <div class="panel-header-title"><span>📊</span> Portföy Dağılımı</div>
            </div>
            
            <div style="display:flex; flex-direction:column; gap:12px;">
                <!-- Kripto -->
                <div>
                    <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px;">
                        <span style="color:#d8b4fe; font-weight:600;">Kripto (Binance)</span>
                        <span id="distCryptoPct" style="color:#fff; font-family:'JetBrains Mono';">0.0%</span>
                    </div>
                    <div style="width:100%; background:rgba(168,85,247,0.1); height:8px; border-radius:4px; overflow:hidden;">
                        <div id="distCryptoBar" style="width:0%; background:linear-gradient(90deg, #9333ea, #d8b4fe); height:100%; border-radius:4px; transition: width 0.5s;"></div>
                    </div>
                </div>
                
                <!-- BIST -->
                <div>
                    <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px;">
                        <span style="color:#86efac; font-weight:600;">BIST 100</span>
                        <span id="distBistPct" style="color:#fff; font-family:'JetBrains Mono';">0.0%</span>
                    </div>
                    <div style="width:100%; background:rgba(74,222,128,0.1); height:8px; border-radius:4px; overflow:hidden;">
                        <div id="distBistBar" style="width:0%; background:linear-gradient(90deg, #16a34a, #4ade80); height:100%; border-radius:4px; transition: width 0.5s;"></div>
                    </div>
                </div>
                
                <!-- NASDAQ -->
                <div>
                    <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px;">
                        <span style="color:#93c5fd; font-weight:600;">NASDAQ</span>
                        <span id="distNasdaqPct" style="color:#fff; font-family:'JetBrains Mono';">0.0%</span>
                    </div>
                    <div style="width:100%; background:rgba(59,130,246,0.1); height:8px; border-radius:4px; overflow:hidden;">
                        <div id="distNasdaqBar" style="width:0%; background:linear-gradient(90deg, #2563eb, #60a5fa); height:100%; border-radius:4px; transition: width 0.5s;"></div>
                    </div>
                </div>
                
                <!-- Nakit (Cash) -->
                <div>
                    <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px;">
                        <span style="color:#cbd5e1; font-weight:600;">Nakit (Rezerv)</span>
                        <span id="distCashPct" style="color:#fff; font-family:'JetBrains Mono';">100.0%</span>
                    </div>
                    <div style="width:100%; background:rgba(203,213,225,0.1); height:8px; border-radius:4px; overflow:hidden;">
                        <div id="distCashBar" style="width:100%; background:linear-gradient(90deg, #64748b, #cbd5e1); height:100%; border-radius:4px; transition: width 0.5s;"></div>
                    </div>
                </div>
                
                <!-- Alt Bilgi -->
                <div style="display:flex; justify-content:space-between; font-size:10px; color:rgba(255,255,255,0.4); margin-top:4px;">
                    <span>Aktif Pozisyonlar Bazlı Tahmini</span>
                </div>
            </div>
        </div>\n'''
    text = text[:idx_start] + replacement + text[idx_end:]

# 2. Extract HTML excluding the final <script> tag
idx_script = text.rfind('<script>')
if idx_script != -1:
    html_part = text[:idx_script]
else:
    html_part = text

# 3. Read dashboard_working_backup.html and extract its pure working JS
with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8', errors='ignore') as f:
    working = f.read()

working_js = re.search(r'<script>(.*?)</script>\s*</body>', working, re.DOTALL)
if not working_js:
    idx_w_script = working.rfind('<script>')
    idx_w_body = working.rfind('</body>')
    working_js_code = working[idx_w_script+8:idx_w_body]
else:
    working_js_code = working_js.group(1)

# Ensure the JS renders to the new HTML IDs
html_part = html_part.replace('id="gridCrypto"', 'id="windowCrypto"')
html_part = html_part.replace('id="gridBist"', 'id="windowBist"')
html_part = html_part.replace('id="gridNasdaq"', 'id="windowNasdaq"')

# Reconstruct the file
final_text = html_part + "<script>\n" + working_js_code + "</script>\n</body>\n</html>"

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(final_text)

print("Rebuilt with PERFECT HTML and PERFECT JS!")
