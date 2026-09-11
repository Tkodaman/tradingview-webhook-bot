import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# 1. Update Clock JS
clock_js = '''
        // Update Clock
        function updateClock() {
            const now = new Date();
            const timeStr = now.toLocaleTimeString('tr-TR', { hour12: false });
            
            const days = ['Pazar', 'Pazartesi', 'Salı', 'Çarşamba', 'Perşembe', 'Cuma', 'Cumartesi'];
            const months = ['Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran', 'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'];
            
            const dateStr = now.getDate() + ' ' + months[now.getMonth()] + ' ' + now.getFullYear() + ' ' + days[now.getDay()];
            
            const start = new Date(now.getFullYear(), 0, 0);
            const diff = now - start;
            const oneDay = 1000 * 60 * 60 * 24;
            const dayOfYear = Math.floor(diff / oneDay);
            const weekOfYear = Math.ceil(dayOfYear / 7);

            document.getElementById('tsClock').innerText = timeStr;
            document.getElementById('tsDate').innerText = dateStr;
            document.getElementById('tsWeek').innerText = 'Hafta ' + weekOfYear;
            document.getElementById('tsYear').innerText = 'Günün ' + dayOfYear + '. günü';
        }
        setInterval(updateClock, 1000);
        updateClock();
'''

html = html.replace('connectWebSocket();\n        fetchLiveMatrix();', clock_js + '\n        connectWebSocket();\n        fetchLiveMatrix();')

# 2. Risk Modal UI
risk_modal_html = '''
    <!-- RISK CONFIRMATION MODAL -->
    <div id="riskModal" class="modal-overlay">
        <div class="modal-content" style="max-width:450px;">
            <div class="modal-header">
                <h2>⚠️ Risk Modu Değişikliği Onayı</h2>
                <button class="modal-close" onclick="closeModal('riskModal')">×</button>
            </div>
            <div style="font-size: 14px; color: #cbd5e1; line-height: 1.5; margin-bottom: 20px;">
                Yapay Zeka Risk ve Frekans Modunu <b id="newRiskModeText" style="color:#fff;">---</b> olarak değiştirmek üzeresiniz.<br><br>
                Bu değişiklik algoritmanın piyasaya girerken arayacağı minimum güven skorunu ve kullanacağı TP/SL oranlarını etkiler. Yeni açılacak pozisyonlar için hemen geçerli olacaktır.
            </div>
            <div style="display:flex; gap:12px; justify-content:flex-end;">
                <button class="btn" style="padding:10px 20px;" onclick="closeModal('riskModal')">İptal</button>
                <button class="btn btn-yellow" style="padding:10px 20px;" onclick="confirmRiskMode()">Değişikliği Onayla</button>
            </div>
        </div>
    </div>
'''

html = html.replace('</body>', risk_modal_html + '\n</body>')

# 3. Risk Mode JS
risk_js = '''
        let pendingRiskMode = null;
        window.setRiskMode = function(mode) {
            pendingRiskMode = mode;
            let text = mode;
            if (mode === 'AGGRESSIVE') text = '🔴 Agresif';
            if (mode === 'NORMAL') text = '🟡 Normal';
            if (mode === 'TIGHT') text = '🔵 Sıkı (Tight)';
            if (mode === 'CONSERVATIVE') text = '🟢 Güvenli (Conservative)';
            
            document.getElementById('newRiskModeText').innerHTML = text;
            openModal('riskModal');
        };

        window.confirmRiskMode = async function() {
            if (!pendingRiskMode) return;
            try {
                const res = await fetch('/api/engine/risk-mode', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ mode: pendingRiskMode })
                });
                const data = await res.json();
                if (data.status === 'success') {
                    showToast('✅ Risk modu başarıyla güncellendi: ' + pendingRiskMode, 'success');
                    
                    // Buton renklerini güncelle
                    document.querySelectorAll('.risk-btn').forEach(btn => btn.classList.remove('active'));
                    document.getElementById('risk-btn-' + pendingRiskMode).classList.add('active');
                    
                    closeModal('riskModal');
                } else {
                    showToast('Güncelleme başarısız!', 'error');
                }
            } catch (err) {
                showToast('API Hatası!', 'error');
            }
        };
'''

# insert risk js before end of script
html = html.replace('</script>\n</body>', risk_js + '\n</script>\n</body>')

# Handle the missing onclick definition which was already 'setRiskMode' 
# Just verified we defined setRiskMode properly

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
