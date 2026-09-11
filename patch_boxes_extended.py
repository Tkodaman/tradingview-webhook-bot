with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace grid minmax
text = text.replace('grid-template-columns: repeat(auto-fill, minmax(65px, 1fr));', 'grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));')

# Now for renderHeatmapBoxes replacement
js_func = '''        function renderHeatmapBoxes(containerId, items, isOpen, tickerId) {
            const container = document.getElementById(containerId);
            const ticker = document.getElementById(tickerId);
            if (!container) return;
            
            container.innerHTML = '';
            
            let tickerText = isOpen ? "" : "🔴 PİYASA KAPALI - ";
            
            items.forEach((item, index) => {
                const confScore = item.confidence_score || 50;
                let bgStyle = "background:rgba(255,255,255,0.05);";
                if(confScore >= 80) bgStyle = "background:linear-gradient(135deg, rgba(34,197,94,0.4) 0%, rgba(21,128,61,0.6) 100%); border-color:#22c55e; box-shadow: 0 0 10px rgba(34,197,94,0.3);";
                else if (confScore >= 60) bgStyle = "background:linear-gradient(135deg, rgba(34,197,94,0.2) 0%, rgba(21,128,61,0.3) 100%); border-color:#16a34a;";
                else if (confScore < 40) bgStyle = "background:linear-gradient(135deg, rgba(239,68,68,0.2) 0%, rgba(185,28,28,0.3) 100%); border-color:#dc2626;";
                
                const closedStyle = isOpen ? "" : "opacity: 0.5; filter: grayscale(80%);";
                const formattedPrice = item.price < 1.0 ? parseFloat(item.price).toFixed(4) : parseFloat(item.price).toFixed(2);
                const rsiStr = item.rsi ? parseFloat(item.rsi).toFixed(1) : '-';
                const volStr = item.volume_ratio ? parseFloat(item.volume_ratio).toFixed(1) : '-';
                const chgColor = item.change_pct >= 0 ? '#4ade80' : '#dc2626';
                const arrow = item.change_pct >= 0 ? "+" : "";
                const aiRec = item.reason || "İzleniyor...";
                
                // Hedef hesaplama (dinamik TP) -> Basit mantık: %3 yukarı (alım) veya güven skoruna orantılı
                let tpFactor = 0.03;
                if(confScore >= 80) tpFactor = 0.045;
                else if(confScore < 40) tpFactor = 0.02;
                const hedefPrice = parseFloat(item.price) * (1 + tpFactor);
                const formattedHedef = hedefPrice < 1.0 ? hedefPrice.toFixed(4) : hedefPrice.toFixed(2);
                
                // Add to ticker
                if (index < 5 && isOpen) {
                    const tArrow = item.change_pct >= 0 ? "🟢" : "🔴";
                    const chgStr = item.change_pct >= 0 ? "+" + item.change_pct + "%" : item.change_pct + "%";
                    tickerText += "[" + item.symbol + ": $" + formattedPrice + " (" + chgStr + ") " + tArrow + " YZ: %" + confScore.toFixed(0) + " Güven, Durum: " + (item.ai_action || item.decision || "İzleniyor") + "] &nbsp;&nbsp;&nbsp;&nbsp;";
                }
                
                const boxHtml = String.fromCharCode(96) + 
                    '<div style="border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; padding: 8px; display:flex; flex-direction:column; gap:6px; transition: all 0.3s ease; cursor:pointer; ' + bgStyle + ' ' + closedStyle + '" onclick="document.getElementById(\\'newPosSymbol\\').value = \\'' + item.symbol + '\\'; openNewPositionModal();">' +
                        '<div style="display:flex; justify-content:space-between; align-items:center;">' +
                            '<span style="font-weight:900; font-size:13px; color:#fff;">' + item.symbol + '</span>' +
                            '<span style="font-size:10px; color:#fbbf24; font-weight:bold;">Güven: %' + confScore.toFixed(1) + '</span>' +
                            '<span style="font-weight:bold; font-size:12px; color:' + chgColor + ';">$' + formattedPrice + ' ' + arrow + '</span>' +
                        '</div>' +
                        '<div style="display:flex; justify-content:space-between; align-items:center; font-size:10px; color:#cbd5e1;">' +
                            '<span>RSI: ' + rsiStr + ' | Hac: ' + volStr + 'x</span>' +
                            '<span style="color:#4ade80; font-weight:bold;">Hedef: $' + formattedHedef + '</span>' +
                        '</div>' +
                        '<div style="font-size:10px; color:#e2e8f0; display:flex; align-items:center; gap:4px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">' +
                            '<i class="fas fa-bolt" style="color:#f472b6;"></i> ' + aiRec +
                        '</div>' +
                    '</div>' + String.fromCharCode(96);
                container.innerHTML += boxHtml;
            });
            
            if (ticker) {
                if (!isOpen) tickerText += "Son kapanış değerleri baz alınmaktadır.";
                ticker.innerHTML = tickerText;
            }
        }'''

# Extract boundaries
start_idx = text.find('function renderHeatmapBoxes(containerId, items, isOpen, tickerId) {')
end_idx = text.find('// RENDER SPECIFIC MARKET GROUP', start_idx)

if start_idx != -1 and end_idx != -1:
    text = text[:start_idx] + js_func + "\n\n        " + text[end_idx:]
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Replaced successfully.")
else:
    print("Could not find boundaries for renderHeatmapBoxes")
