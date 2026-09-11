import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Update renderHeatmapBoxes to match the sleek dark theme with left borders
new_render_js = '''
        if (!window.heatmapPrevPrices) window.heatmapPrevPrices = {};

        function renderHeatmapBoxes(containerId, items, isOpen, tickerId) {
            const container = document.getElementById(containerId);
            const ticker = document.getElementById(tickerId);
            if (!container) return;
            
            container.innerHTML = '';
            
            let tickerText = isOpen ? "" : "🔴 PİYASA KAPALI - ";
            
            items.forEach((item, index) => {
                const confScore = item.confidence_score || 50;
                
                const prev = window.heatmapPrevPrices[item.symbol];
                let flashClass = "";
                let dirArrow = "";
                if (prev !== undefined && isOpen) {
                    if (item.price > prev) { flashClass = "flash-up"; dirArrow = "↑"; }
                    else if (item.price < prev) { flashClass = "flash-down"; dirArrow = "↓"; }
                }
                window.heatmapPrevPrices[item.symbol] = item.price;
                
                // Color logic
                const isUp = item.change_pct >= 0;
                const chgColor = isUp ? '#4ade80' : '#f43f5e';
                const borderColor = isUp ? 'rgba(74, 222, 128, 0.7)' : 'rgba(244, 63, 94, 0.7)';
                const bgGradient = isUp ? 'linear-gradient(90deg, rgba(74,222,128,0.15) 0%, rgba(0,0,0,0.3) 20%)' : 'linear-gradient(90deg, rgba(244,63,94,0.15) 0%, rgba(0,0,0,0.3) 20%)';
                
                const closedStyle = isOpen ? "" : "opacity: 0.4; filter: grayscale(80%);";
                const formattedPrice = item.price < 1.0 ? parseFloat(item.price).toFixed(4) : parseFloat(item.price).toFixed(2);
                const rsiStr = item.rsi ? parseFloat(item.rsi).toFixed(1) : '-';
                const volStr = item.volume_ratio ? parseFloat(item.volume_ratio).toFixed(1) : '-';
                
                // If it doesn't have an arrow yet, default based on change_pct
                if (!dirArrow) dirArrow = isUp ? "↑" : "↓";
                
                const aiRec = item.reason || "İzleniyor...";
                
                // Hedef hesaplama (dinamik TP) -> Basit mantık: %3 yukarı (alım) veya güven skoruna orantılı
                let tpFactor = 0.03;
                if(confScore >= 80) tpFactor = 0.045;
                else if(confScore < 40) tpFactor = 0.02;
                const hedefPrice = parseFloat(item.price) * (1 + (isUp ? tpFactor : -tpFactor));
                const formattedHedef = hedefPrice < 1.0 ? hedefPrice.toFixed(4) : hedefPrice.toFixed(2);
                
                // Add to ticker
                if (index < 5 && isOpen) {
                    const tArrow = isUp ? "🟢" : "🔴";
                    const chgStr = isUp ? "+" + item.change_pct + "%" : item.change_pct + "%";
                    tickerText += "[" + item.symbol + ": $" + formattedPrice + " (" + chgStr + ") " + tArrow + " YZ: %" + confScore.toFixed(0) + " Güven] &nbsp;&nbsp;&nbsp;&nbsp;";
                }
                
                const boxHtml = String.fromCharCode(96) + 
                    '<div class="' + flashClass + '" style="border-radius: 8px; border: 1px solid rgba(255,255,255,0.05); border-left: 4px solid ' + borderColor + '; padding: 8px; display:flex; flex-direction:column; gap:6px; transition: all 0.3s ease; cursor:pointer; background: ' + bgGradient + '; ' + closedStyle + ' box-shadow: 0 4px 6px rgba(0,0,0,0.2);" onclick="document.getElementById(\\'newPosSymbol\\').value = \\'' + item.symbol + '\\'; openNewPositionModal();">' +
                        '<div style="display:flex; justify-content:space-between; align-items:center;">' +
                            '<div style="display:flex; align-items:center; gap:6px;">' +
                                '<span style="font-weight:700; font-size:13px; color:#fbbf24;">' + item.symbol + '</span>' +
                                '<span style="font-size:10px; color:#fbbf24; background: rgba(251,191,36,0.15); padding: 2px 5px; border-radius:4px; font-weight:600;">Güven: %' + confScore.toFixed(1) + '</span>' +
                            '</div>' +
                            '<span style="font-weight:800; font-size:13px; color:' + chgColor + ';">$' + formattedPrice + ' ' + dirArrow + '</span>' +
                        '</div>' +
                        '<div style="display:flex; justify-content:space-between; align-items:center; font-size:10px; color:#cbd5e1; font-weight: 500;">' +
                            '<span>RSI: <span style="color:#fff;">' + rsiStr + '</span> | Hac: <span style="color:#fff;">' + volStr + 'x</span></span>' +
                            '<span style="color:#4ade80;">Hedef: $' + formattedHedef + '</span>' +
                        '</div>' +
                        '<div style="font-size:10px; color:#94a3b8; display:flex; align-items:center; gap:5px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">' +
                            '<span style="font-size:10px;">🎯</span> ' + aiRec +
                        '</div>' +
                    '</div>' + String.fromCharCode(96);
                container.innerHTML += boxHtml;
            });
            
            if (ticker) {
                if (!isOpen) tickerText += "Son kapanış değerleri baz alınmaktadır.";
                ticker.innerHTML = tickerText;
            }
        }
'''

html = re.sub(r'if \(!window\.heatmapPrevPrices\).*?ticker\.innerHTML = tickerText;\s*\}\s*\}', new_render_js, html, flags=re.DOTALL)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
