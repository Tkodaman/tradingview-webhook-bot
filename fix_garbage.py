with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find("You're in planning mode. Exercise judgement")
if idx != -1:
    idx_start = text.rfind('<div class="panel"', 0, idx)
    idx_end = text.find('</div>\n        </div>', idx)
    if idx_start != -1 and idx_end != -1:
        # We will replace everything from idx_start to idx_end + 14
        replacement = '''<div class="panel" style="padding:16px;">
            <div class="panel-header" style="margin-bottom:12px;">
                <div class="panel-header-title"><span>📊</span> Portföy Dağılımı</div>
            </div>
            
            <div style="display:flex; flex-direction:column; gap:12px;">
                <!-- Kripto -->
                <div>
                    <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px;">
                        <span style="color:#d8b4fe; font-weight:600;">Kripto (Binance)</span>
                        <span id="distCryptoPct" style="color:#fff; font-family:'JetBrains Mono';">45.2%</span>
                    </div>
                    <div style="width:100%; background:rgba(168,85,247,0.1); height:8px; border-radius:4px; overflow:hidden;">
                        <div id="distCryptoBar" style="width:45.2%; background:linear-gradient(90deg, #9333ea, #d8b4fe); height:100%; border-radius:4px;"></div>
                    </div>
                </div>
                
                <!-- BIST -->
                <div>
                    <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px;">
                        <span style="color:#86efac; font-weight:600;">BIST 100</span>
                        <span id="distBistPct" style="color:#fff; font-family:'JetBrains Mono';">32.8%</span>
                    </div>
                    <div style="width:100%; background:rgba(74,222,128,0.1); height:8px; border-radius:4px; overflow:hidden;">
                        <div id="distBistBar" style="width:32.8%; background:linear-gradient(90deg, #16a34a, #4ade80); height:100%; border-radius:4px;"></div>
                    </div>
                </div>
                
                <!-- NASDAQ -->
                <div>
                    <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px;">
                        <span style="color:#93c5fd; font-weight:600;">NASDAQ</span>
                        <span id="distNasdaqPct" style="color:#fff; font-family:'JetBrains Mono';">12.0%</span>
                    </div>
                    <div style="width:100%; background:rgba(59,130,246,0.1); height:8px; border-radius:4px; overflow:hidden;">
                        <div id="distNasdaqBar" style="width:12.0%; background:linear-gradient(90deg, #2563eb, #60a5fa); height:100%; border-radius:4px;"></div>
                    </div>
                </div>
                
                <!-- Nakit (Cash) -->
                <div>
                    <div style="display:flex; justify-content:space-between; font-size:12px; margin-bottom:4px;">
                        <span style="color:#cbd5e1; font-weight:600;">Nakit (Rezerv)</span>
                        <span id="distCashPct" style="color:#fff; font-family:'JetBrains Mono';">10.0%</span>
                    </div>
                    <div style="width:100%; background:rgba(203,213,225,0.1); height:8px; border-radius:4px; overflow:hidden;">
                        <div id="distCashBar" style="width:10.0%; background:linear-gradient(90deg, #64748b, #cbd5e1); height:100%; border-radius:4px;"></div>
                    </div>
                </div>
                
                <!-- Alt Bilgi -->
                <div style="display:flex; justify-content:space-between; font-size:10px; color:var(--text-muted); margin-top:4px;">
                    <span>Aktif Pozisyonlar Bazlı Tahmini</span>
                    <span id="distTotalValue" style="color:#a78bfa; font-family:'JetBrains Mono'; font-weight:600;">$ 0.00</span>
                </div>
            </div>
        </div>'''
        
        text = text[:idx_start] + replacement + text[idx_end+14:]
        with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Replaced successfully!")
else:
    print("Garbage not found!")
