with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re

new_js = '''
                    if (msg.type === 'LIVE_MARKET') {
'''

inject_js = '''
                    if (msg.type === 'TRADE_UPDATE') {
                        console.log("Alpaca Update:", msg);
                        // Optional notification could go here if user wants a visual toast.
                        // Position tables refresh automatically via LIVE_MARKET anyway.
                    }
                    if (msg.type === 'RISK_UPDATE') {
                        const allBtns = document.querySelectorAll('.risk-btn');
                        allBtns.forEach(b => b.classList.remove('active'));
                        
                        let targetBtnId = "";
                        if(msg.multiplier === 1.2) targetBtnId = "riskAggressive";
                        else if(msg.multiplier === 1.0) targetBtnId = "riskNormal";
                        else if(msg.multiplier === 0.5) targetBtnId = "riskConservative";
                        else if(msg.multiplier === 0.2) targetBtnId = "riskSafe";
                        
                        if(targetBtnId) {
                            const btn = document.getElementById(targetBtnId);
                            if(btn) btn.classList.add('active');
                        }
                    }
                    
                    if (msg.type === 'LIVE_MARKET') {
'''

text = text.replace(new_js, inject_js)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)
