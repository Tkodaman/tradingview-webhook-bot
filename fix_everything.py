with open('templates/dashboard_final.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# 1. We replace the garbage inside the Portfoy panel
idx_garbage = text.find("You're in planning mode. Exercise judgement")
if idx_garbage != -1:
    idx_start = text.rfind('<div class="panel"', 0, idx_garbage)
    # The garbage text spans multiple lines. Let's find the Risk panel after it
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

# 2. Fix JS IDs
text = text.replace("renderMarketGroup('gridCrypto'", "renderMarketGroup('windowCrypto'")
text = text.replace("renderMarketGroup('gridBist'", "renderMarketGroup('windowBist'")
text = text.replace("renderMarketGroup('gridNasdaq'", "renderMarketGroup('windowNasdaq'")

# 3. Fix JS syntax error Islem #
import re
text = re.sub(r"return idx === 0 \? 'Start' : .*?;", "return idx === 0 ? 'Start' : 'Islem #' + idx;", text)

# 4. Remove any other EPHEMERAL_MESSAGE tags that are just stray strings
# Because they might not have closing tags, we just remove the known phrases
text = text.replace("<EPHEMERAL_MESSAGE>", "")
text = text.replace("</EPHEMERAL_MESSAGE>", "")
text = text.replace("<planning_mode>", "")
text = text.replace("</planning_mode>", "")
text = text.replace("<bash_command_reminder>", "")
text = text.replace("</bash_command_reminder>", "")
text = re.sub(r"You're in planning mode\..*?Feedback\.\n?", "", text, flags=re.DOTALL)

# 5. Fix truncation in JS at the very end
idx_trunc = text.find("borderColor = 'rgba\n<truncated")
if idx_trunc != -1:
    text = text[:idx_trunc] + "borderColor = 'rgba(234,179,8,0.18)';\n}\n}\n</script>\n</body>\n</html>"
else:
    # also handle if <truncated was already removed
    idx_rgba = text.find("borderColor = 'rgba\n")
    if idx_rgba != -1:
        text = text[:idx_rgba] + "borderColor = 'rgba(234,179,8,0.18)';\n}\n}\n</script>\n</body>\n</html>"

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Restored 286KB dashboard and fixed Portfoy!")
