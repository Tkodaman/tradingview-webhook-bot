with open('templates/cand_perfect2.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx_start = text.find('You\'re in planning mode')
if idx_start != -1:
    idx_div = text.rfind('<div class="panel"', 0, idx_start)
    idx_risk = text.find('Risk Parametreleri', idx_start)
    idx_div_end = text.rfind('<div class="panel"', idx_start, idx_risk)
    
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
        
    text = text[:idx_div] + replacement + text[idx_div_end:]

# Also replace <EPHEMERAL_MESSAGE> anywhere else if it exists
import re
text = re.sub(r'<EPHEMERAL_MESSAGE>.*?</EPHEMERAL_MESSAGE>', '', text, flags=re.DOTALL)

with open('templates/cand_perfect_fixed.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Created cand_perfect_fixed.html with full layout!")
