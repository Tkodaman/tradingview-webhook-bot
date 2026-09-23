with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Let's find the Seans Saati panel
idx_seans = text.find('Seans Saati & Countdown')
# Find the end of the Seans Saati panel
idx_seans_end = text.find('</div>\r\n        </div>', idx_seans)
if idx_seans_end == -1:
    idx_seans_end = text.find('</div>\n        </div>', idx_seans)
if idx_seans_end == -1:
    idx_seans_end = text.find('</div>        </div>', idx_seans)

# Find the start of the Risk Parametreleri panel
idx_risk = text.find('Risk Parametreleri')
idx_risk_start = text.rfind('<div class="panel"', 0, idx_risk)

replacement = '''
        <!-- Portföy Dağılımı (Orta Panel) -->
        <div class="panel" style="padding:16px;">
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
                    <span>Aktif Pozisyonlar Bazlı Tahmini Dağılım</span>
                </div>
            </div>
        </div>
'''

if idx_seans != -1 and idx_risk != -1:
    # We replace everything between the end of Seans panel and the start of Risk panel
    new_text = text[:idx_seans_end+16] + replacement + text[idx_risk_start:]
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("Injected Portfolio perfectly!")
else:
    print("Indices not found!")
