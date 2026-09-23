with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

modal_html = '''
    <!-- Hızlı Pozisyon Aç Modal -->
    <div id="quickOrderModal" class="modal-overlay" style="display:none; position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.6); z-index:9999; justify-content:center; align-items:center;">
        <div class="modal-box" style="background:#131722; border:1px solid #334155; border-radius:12px; padding:24px; max-width:400px; width:100%; box-shadow:0 10px 40px rgba(0,0,0,0.5);">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:20px;">
                <h3 style="margin:0; color:#f8fafc;">Hızlı Pozisyon Aç</h3>
                <button onclick="document.getElementById('quickOrderModal').style.display='none'" style="background:transparent; border:none; color:#94a3b8; cursor:pointer; font-size:18px;">&times;</button>
            </div>
            
            <div style="display:flex; flex-direction:column; gap:16px;">
                <div>
                    <label style="color:#cbd5e1; font-size:12px; display:block; margin-bottom:6px;">Sembol (Örn: AAPL, BTCUSDT)</label>
                    <input type="text" id="qoSymbol" style="width:100%; background:#0f121a; border:1px solid #334155; color:#fff; padding:10px; border-radius:6px; box-sizing:border-box;">
                </div>
                
                <div style="display:flex; gap:12px;">
                    <div style="flex:1;">
                        <label style="color:#cbd5e1; font-size:12px; display:block; margin-bottom:6px;">Yön</label>
                        <select id="qoSide" style="width:100%; background:#0f121a; border:1px solid #334155; color:#fff; padding:10px; border-radius:6px; box-sizing:border-box;">
                            <option value="BUY">BUY (Uzun)</option>
                            <option value="SELL">SELL (Kısa)</option>
                        </select>
                    </div>
                    <div style="flex:1;">
                        <label style="color:#cbd5e1; font-size:12px; display:block; margin-bottom:6px;">Bütçe ($)</label>
                        <input type="number" id="qoCapital" value="100" style="width:100%; background:#0f121a; border:1px solid #334155; color:#fff; padding:10px; border-radius:6px; box-sizing:border-box;">
                    </div>
                </div>
                
                <div style="display:flex; gap:12px;">
                    <div style="flex:1;">
                        <label style="color:#cbd5e1; font-size:12px; display:block; margin-bottom:6px;">Kâr Al (%)</label>
                        <input type="number" id="qoTpPct" value="3.0" step="0.1" style="width:100%; background:#0f121a; border:1px solid #334155; color:#fff; padding:10px; border-radius:6px; box-sizing:border-box;">
                    </div>
                    <div style="flex:1;">
                        <label style="color:#cbd5e1; font-size:12px; display:block; margin-bottom:6px;">Zarar Kes (%)</label>
                        <input type="number" id="qoSlPct" value="1.5" step="0.1" style="width:100%; background:#0f121a; border:1px solid #334155; color:#fff; padding:10px; border-radius:6px; box-sizing:border-box;">
                    </div>
                </div>
                
                <button onclick="submitNewPosition()" class="btn btn-green" style="width:100%; padding:12px; font-weight:bold; margin-top:10px;">Emri Piyasaya İlet</button>
            </div>
        </div>
    </div>
'''

js_code = '''
    // =========================================================
    // ALPACA CLOCK AND QUICK ORDER INTEGRATION
    // =========================================================
    let alpacaClockOffset = 0;
    
    async function fetchAlpacaClock() {
        try {
            const res = await fetch('/api/positions/clock');
            const data = await res.json();
            if (data.status === 'success' || data.status === 'fallback') {
                const alpacaTime = new Date(data.timestamp).getTime();
                const localTime = new Date().getTime();
                alpacaClockOffset = alpacaTime - localTime;
                
                // Update statuses based on data
                const isMarketOpen = data.is_open;
                const badgeNasdaq = document.getElementById('badgeNasdaqStatus');
                if (badgeNasdaq) {
                    badgeNasdaq.className = isMarketOpen ? "window-status-badge status-open" : "window-status-badge status-closed";
                    badgeNasdaq.innerHTML = isMarketOpen ? '<span class="live-dot"></span> PİYASA AÇIK' : 'PİYASA KAPALI';
                }
            }
        } catch (e) {
            console.error("Alpaca clock fetch error", e);
        }
    }
    
    function updateClockUI() {
        const now = new Date(new Date().getTime() + alpacaClockOffset);
        
        const dateSpan = document.getElementById('tsDate');
        if (dateSpan) dateSpan.innerText = now.toLocaleDateString('tr-TR', { day: '2-digit', month: '2-digit', year: 'numeric' });
        
        const clockSpan = document.getElementById('tsClock');
        if (clockSpan) clockSpan.innerText = now.toLocaleTimeString('tr-TR', { hour12: false });
        
        // Simple logic for week/day
        const weekSpan = document.getElementById('tsWeek');
        if (weekSpan) {
            const start = new Date(now.getFullYear(), 0, 1);
            const days = Math.floor((now - start) / (24 * 60 * 60 * 1000));
            const weekNumber = Math.ceil((now.getDay() + 1 + days) / 7);
            weekSpan.innerText = Hafta ;
        }
        
        const yearSpan = document.getElementById('tsYear');
        if (yearSpan) {
            const start = new Date(now.getFullYear(), 0, 1);
            const days = Math.floor((now - start) / (24 * 60 * 60 * 1000)) + 1;
            yearSpan.innerText = Günün . günü;
        }
    }
    
    // Initial fetch and start interval
    fetchAlpacaClock();
    setInterval(updateClockUI, 1000); // UI updates every second
    setInterval(fetchAlpacaClock, 60000); // Resync offset every 60s
    
    // Quick Order Modal
    function openNewPositionModal() {
        const modal = document.getElementById('quickOrderModal');
        if (modal) {
            modal.style.display = 'flex';
        }
    }
    
    async function submitNewPosition() {
        const symbol = document.getElementById('qoSymbol').value.toUpperCase();
        const side = document.getElementById('qoSide').value;
        const capital = parseFloat(document.getElementById('qoCapital').value);
        const tpPct = parseFloat(document.getElementById('qoTpPct').value);
        const slPct = parseFloat(document.getElementById('qoSlPct').value);
        
        if (!symbol) {
            showToast("Lütfen bir sembol giriniz.", "error");
            return;
        }
        
        try {
            const res = await fetch('/api/positions/open', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    symbol: symbol,
                    side: side,
                    capital: capital,
                    tp_pct: tpPct,
                    sl_pct: slPct
                })
            });
            
            const data = await res.json();
            if (res.ok) {
                showToast(${symbol} için pozisyon açıldı., "success");
                document.getElementById('quickOrderModal').style.display = 'none';
                if (typeof fetchPositions === 'function') fetchPositions();
            } else {
                showToast(Hata: , "error");
            }
        } catch (e) {
            showToast("Bağlantı hatası.", "error");
        }
    }
    
    async function closePosition(posId) {
        if(!confirm(Bu pozisyonu () kapatmak istediğinize emin misiniz?)) return;
        
        try {
            const res = await fetch(/api/positions/close/, { method: 'POST' });
            const data = await res.json();
            
            if (res.ok) {
                showToast("Pozisyon başarıyla kapatıldı.", "success");
                if (typeof fetchPositions === 'function') fetchPositions();
            } else {
                showToast(Hata: , "error");
            }
        } catch(e) {
            showToast("Bağlantı hatası.", "error");
        }
    }
'''

# We will inject modal_html before </body>
if 'quickOrderModal' not in text:
    idx_body = text.rfind('</body>')
    text = text[:idx_body] + modal_html + '\n' + text[idx_body:]

# We will inject js_code before </script>\n</body>
if 'submitNewPosition' not in text:
    idx_script = text.rfind('</script>')
    text = text[:idx_script] + js_code + '\n' + text[idx_script:]

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Added modal and js logic to dashboard.html")
