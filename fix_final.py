with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_block = '''                // RENDER HEATMAP BOXES
                renderHeatmapBoxes('top15CryptoBody', data.grouped.CRYPTO || [], cryptoInfo.is_open);
                renderHeatmapBoxes('top15BistBody', data.grouped.BIST || [], bistInfo.is_open);
                renderHeatmapBoxes('top15NasdaqBody', data.grouped.NASDAQ || [], nasdaqInfo.is_open);

                // RENDER EACH GRID SEPARATELY
                renderMarketGroup('gridCrypto', data.grouped.CRYPTO || [], cryptoInfo.is_open, 'cryptoStatsCount');
                renderMarketGroup('gridBist', data.grouped.BIST || [], bistInfo.is_open, 'bistStatsCount');
                renderMarketGroup('gridNasdaq', data.grouped.NASDAQ || [], nasdaqInfo.is_open, 'nasdaqStatsCount');

            } catch (err) {
                console.error("fetchLiveMatrix error:", err);
            }
        }

        function renderHeatmapBoxes(containerId, items, isOpen) {
            const container = document.getElementById(containerId);
            if (!container) return;
            
            container.innerHTML = '';
            
            items.forEach(item => {
                const confScore = item.confidence_score || 50;
                let bgStyle = "background:rgba(255,255,255,0.05);";
                if(confScore >= 80) bgStyle = "background:linear-gradient(135deg, rgba(34,197,94,0.4) 0%, rgba(21,128,61,0.6) 100%); border-color:#22c55e; box-shadow: 0 0 10px rgba(34,197,94,0.3);";
                else if (confScore >= 60) bgStyle = "background:linear-gradient(135deg, rgba(34,197,94,0.2) 0%, rgba(21,128,61,0.3) 100%); border-color:#16a34a;";
                else if (confScore < 40) bgStyle = "background:linear-gradient(135deg, rgba(239,68,68,0.2) 0%, rgba(185,28,28,0.3) 100%); border-color:#dc2626;";
                
                const closedStyle = isOpen ? "" : "opacity: 0.5; filter: grayscale(80%);";
                
                const formattedPrice = item.price < 1.0 ? parseFloat(item.price).toFixed(4) : parseFloat(item.price).toFixed(2);
                
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
        }
'''

# The corrupted lines start exactly at // RENDER HEATMAP BOXES
start_idx = -1
end_idx = -1
for i, line in enumerate(lines):
    if "// RENDER HEATMAP BOXES" in line:
        start_idx = i
    if "function renderMarketGroup(" in line:
        end_idx = i
        break

if start_idx != -1 and end_idx != -1:
    lines_to_keep = lines[:start_idx] + [new_block + "\n"] + lines[end_idx-1:]
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.writelines(lines_to_keep)
    print("Fixed.")
else:
    print("Could not find start/end indices")
