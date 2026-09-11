with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Add tickers above the bodies
html_replace_crypto = '''<div style="font-size:12px; font-weight:bold; margin-bottom:8px; color:#4ade80; text-align:center;">🪙 Kripto Piyasası</div>
                <div style="overflow:hidden; white-space:nowrap; margin-bottom:8px; background:rgba(0,0,0,0.2); border-radius:4px; padding:4px 0;">
                    <marquee id="tickerCrypto" scrollamount="4" style="font-size:10px; color:#94a3b8; font-family: 'JetBrains Mono', monospace;">Veriler Bekleniyor...</marquee>
                </div>
                <div id="top15CryptoBody"'''

html_replace_bist = '''<div style="font-size:12px; font-weight:bold; margin-bottom:8px; color:#38bdf8; text-align:center;">🇹🇷 BIST 100/30</div>
                <div style="overflow:hidden; white-space:nowrap; margin-bottom:8px; background:rgba(0,0,0,0.2); border-radius:4px; padding:4px 0;">
                    <marquee id="tickerBist" scrollamount="4" style="font-size:10px; color:#94a3b8; font-family: 'JetBrains Mono', monospace;">Veriler Bekleniyor...</marquee>
                </div>
                <div id="top15BistBody"'''

html_replace_nasdaq = '''<div style="font-size:12px; font-weight:bold; margin-bottom:8px; color:#f472b6; text-align:center;">🇺🇸 NASDAQ Mega-Cap</div>
                <div style="overflow:hidden; white-space:nowrap; margin-bottom:8px; background:rgba(0,0,0,0.2); border-radius:4px; padding:4px 0;">
                    <marquee id="tickerNasdaq" scrollamount="4" style="font-size:10px; color:#94a3b8; font-family: 'JetBrains Mono', monospace;">Veriler Bekleniyor...</marquee>
                </div>
                <div id="top15NasdaqBody"'''

text = text.replace('<div style="font-size:12px; font-weight:bold; margin-bottom:8px; color:#4ade80; text-align:center;">🪙 Kripto Piyasası</div>\n                <div id="top15CryptoBody"', html_replace_crypto)
text = text.replace('<div style="font-size:12px; font-weight:bold; margin-bottom:8px; color:#38bdf8; text-align:center;">🇹🇷 BIST 100/30</div>\n                <div id="top15BistBody"', html_replace_bist)
text = text.replace('<div style="font-size:12px; font-weight:bold; margin-bottom:8px; color:#f472b6; text-align:center;">🇺🇸 NASDAQ Mega-Cap</div>\n                <div id="top15NasdaqBody"', html_replace_nasdaq)


# Update renderHeatmapBoxes to populate the tickers
js_func = '''
        function renderHeatmapBoxes(containerId, items, isOpen, tickerId) {
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
                
                // Add to ticker (only first 5 items to keep it readable)
                if (index < 5 && isOpen) {
                    const arrow = item.change_pct >= 0 ? "🟢" : "🔴";
                    const chgStr = item.change_pct >= 0 ? "+" + item.change_pct + "%" : item.change_pct + "%";
                    const aiRec = item.ai_action || item.decision || "İzleniyor";
                    tickerText += [: {formattedPrice} ()  YZ: % Güven, Durum: ] &nbsp;&nbsp;&nbsp;&nbsp;;
                }
                
                const boxHtml = String.fromCharCode(96) + 
                    '<div style="border: 1px solid rgba(255,255,255,0.1); border-radius: 6px; padding: 6px; display:flex; flex-direction:column; align-items:center; justify-content:center; text-align:center; transition: all 0.3s ease; cursor:pointer; ' + bgStyle + ' ' + closedStyle + '" onclick="document.getElementById(\\'newPosSymbol\\').value = \\'' + item.symbol + '\\'; openNewPositionModal();">' +
                        '<div style="font-weight:900; font-size:12px; color:#fff; letter-spacing:0.5px;">' + item.symbol + '</div>' +
                        '<div style="font-size:10px; color:#cbd5e1; font-family:\\'JetBrains Mono\\', monospace; margin: 3px 0;">$' + formattedPrice + '</div>' +
                        '<div style="font-size:11px; font-weight:bold; color: #fff;">' +
                            '%' + confScore.toFixed(0) + ' <i class="fas fa-robot" style="font-size:9px; opacity:0.8;"></i>' +
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

# Update the JS function signature and calls
text = text.replace("renderHeatmapBoxes('top15CryptoBody', data.grouped.CRYPTO || [], cryptoInfo.is_open);", "renderHeatmapBoxes('top15CryptoBody', data.grouped.CRYPTO || [], cryptoInfo.is_open, 'tickerCrypto');")
text = text.replace("renderHeatmapBoxes('top15BistBody', data.grouped.BIST || [], bistInfo.is_open);", "renderHeatmapBoxes('top15BistBody', data.grouped.BIST || [], bistInfo.is_open, 'tickerBist');")
text = text.replace("renderHeatmapBoxes('top15NasdaqBody', data.grouped.NASDAQ || [], nasdaqInfo.is_open);", "renderHeatmapBoxes('top15NasdaqBody', data.grouped.NASDAQ || [], nasdaqInfo.is_open, 'tickerNasdaq');")

# We need to replace the old renderHeatmapBoxes function block
start_idx = text.find('function renderHeatmapBoxes(containerId, items, isOpen) {')
end_idx = text.find('// RENDER SPECIFIC MARKET GROUP', start_idx)
if start_idx != -1 and end_idx != -1:
    text = text[:start_idx] + js_func + "\n        " + text[end_idx:]
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Updated Dashboard Tickers successfully.")
else:
    print("Could not find renderHeatmapBoxes function block.")

