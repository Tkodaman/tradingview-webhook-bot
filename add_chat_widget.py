import os

chat_widget_html = '''
<!-- AI ANALYST CHAT WIDGET -->
<style>
#aiChatWidget {
    position: fixed;
    bottom: 30px;
    right: 30px;
    width: 350px;
    background: #111827;
    border: 1px solid rgba(139, 92, 246, 0.4);
    border-radius: 12px;
    box-shadow: 0 10px 40px rgba(0, 0, 0, 0.8), 0 0 20px rgba(139, 92, 246, 0.2);
    display: flex;
    flex-direction: column;
    z-index: 99999;
    overflow: hidden;
    font-family: 'Outfit', sans-serif;
    transition: transform 0.3s ease, opacity 0.3s ease;
}
#aiChatHeader {
    background: linear-gradient(135deg, #1c1f2e 0%, #0f1117 100%);
    padding: 12px 16px;
    border-bottom: 1px solid rgba(139, 92, 246, 0.2);
    display: flex;
    justify-content: space-between;
    align-items: center;
    cursor: pointer;
}
#aiChatBody {
    height: 300px;
    padding: 15px;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 10px;
    background: rgba(0,0,0,0.2);
}
#aiChatInputContainer {
    padding: 12px;
    background: #1c1f2e;
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    display: flex;
    gap: 8px;
}
#aiChatInput {
    flex: 1;
    background: #0f1117;
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 6px;
    padding: 8px 12px;
    color: #fff;
    font-size: 13px;
    outline: none;
}
#aiChatInput:focus {
    border-color: #8b5cf6;
}
#aiChatBtn {
    background: #8b5cf6;
    color: #fff;
    border: none;
    border-radius: 6px;
    padding: 0 16px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.2s;
}
#aiChatBtn:hover {
    background: #7c3aed;
}
.chat-msg {
    max-width: 85%;
    padding: 10px 14px;
    border-radius: 8px;
    font-size: 13px;
    line-height: 1.5;
    word-wrap: break-word;
}
.chat-user {
    align-self: flex-end;
    background: #3b82f6;
    color: #fff;
    border-bottom-right-radius: 2px;
}
.chat-ai {
    align-self: flex-start;
    background: #1f2937;
    border: 1px solid rgba(255,255,255,0.1);
    color: #cbd5e1;
    border-bottom-left-radius: 2px;
}
.typing-indicator {
    align-self: flex-start;
    color: #a78bfa;
    font-size: 11px;
    font-style: italic;
    display: none;
}
</style>

<div id="aiChatWidget">
    <div id="aiChatHeader" onclick="toggleAiChat()">
        <div style="display:flex; align-items:center; gap:8px;">
            <span style="font-size: 18px;">🤖</span>
            <span style="color: #c4b5fd; font-weight: 600; font-size: 14px; letter-spacing: 0.5px;">Gölge Zeka (LLM)</span>
        </div>
        <span id="aiChatToggleIcon" style="color: #94a3b8; font-size: 12px;">▼</span>
    </div>
    <div id="aiChatContent">
        <div id="aiChatBody">
            <div class="chat-msg chat-ai">Merhaba, ben Gölge Zeka. Astra-6 motoruna bağlıyım. Analiz veya öngörü için bana her şeyi sorabilirsiniz.</div>
        </div>
        <div class="typing-indicator" id="aiTypingIndicator">Gölge Zeka düşünüyor...</div>
        <div id="aiChatInputContainer">
            <input type="text" id="aiChatInput" placeholder="Mesajınızı yazın..." onkeypress="if(event.key === 'Enter') sendAiMessage()">
            <button id="aiChatBtn" onclick="sendAiMessage()">Gönder</button>
        </div>
    </div>
</div>

<script>
let isChatOpen = true;
function toggleAiChat() {
    isChatOpen = !isChatOpen;
    document.getElementById('aiChatContent').style.display = isChatOpen ? 'block' : 'none';
    document.getElementById('aiChatToggleIcon').innerText = isChatOpen ? '▼' : '▲';
}

async function sendAiMessage() {
    const input = document.getElementById('aiChatInput');
    const msg = input.value.trim();
    if(!msg) return;
    
    input.value = '';
    
    // Add user message to UI
    const body = document.getElementById('aiChatBody');
    const userDiv = document.createElement('div');
    userDiv.className = 'chat-msg chat-user';
    userDiv.innerText = msg;
    body.appendChild(userDiv);
    body.scrollTop = body.scrollHeight;
    
    document.getElementById('aiTypingIndicator').style.display = 'block';
    
    try {
        const response = await fetch('/api/agent/custom', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({ prompt: msg })
        });
        
        const data = await response.json();
        
        // Add AI message to UI
        const aiDiv = document.createElement('div');
        aiDiv.className = 'chat-msg chat-ai';
        // Parse basic markdown if needed or just use innerText
        aiDiv.innerHTML = data.detailed_report ? data.detailed_report.replace(/\\n/g, '<br>') : 'Hata: Yanıt alınamadı.';
        body.appendChild(aiDiv);
        
        // Update token tracker
        if(data.structured_data && data.structured_data.tokens_used) {
            if(typeof consumeTokens === 'function') consumeTokens(data.structured_data.tokens_used);
        }
    } catch(e) {
        const errDiv = document.createElement('div');
        errDiv.className = 'chat-msg chat-ai';
        errDiv.style.color = '#ef4444';
        errDiv.innerText = 'Bağlantı hatası: ' + e.message;
        body.appendChild(errDiv);
    } finally {
        document.getElementById('aiTypingIndicator').style.display = 'none';
        body.scrollTop = body.scrollHeight;
    }
}
</script>
<!-- END AI ANALYST CHAT WIDGET -->
'''

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Make sure we don't inject multiple times
if "AI ANALYST CHAT WIDGET" not in html:
    html = html.replace('</body>', chat_widget_html + '\n</body>')
    with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
        f.write(html)
    print("Chat widget added to dashboard.")
else:
    print("Chat widget already exists.")

