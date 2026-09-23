import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

new_send_message = '''async function sendAiMessage() {
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
    
    // Add AI message container
    const aiDiv = document.createElement('div');
    aiDiv.className = 'chat-msg chat-ai';
    aiDiv.innerHTML = '';
    body.appendChild(aiDiv);
    
    try {
        const source = new EventSource(`/api/agent/stream?prompt=${encodeURIComponent(msg)}`);
        
        source.onmessage = function(event) {
            document.getElementById('aiTypingIndicator').style.display = 'none';
            if (event.data === '[DONE]') {
                source.close();
                // Estimate tokens: 1 token per roughly 4 chars as a very basic simulation
                if(typeof consumeTokens === 'function') {
                    const estimatedTokens = Math.floor(aiDiv.innerText.length / 4) + Math.floor(msg.length / 4);
                    if (estimatedTokens > 0) consumeTokens(estimatedTokens);
                }
            } else {
                // Append chunk
                aiDiv.innerHTML += event.data;
                body.scrollTop = body.scrollHeight;
            }
        };
        
        source.onerror = function(err) {
            document.getElementById('aiTypingIndicator').style.display = 'none';
            source.close();
            // Only show error if we got nothing
            if (aiDiv.innerHTML === '') {
                aiDiv.style.color = '#ef4444';
                aiDiv.innerText = 'Bağlantı koptu veya hata oluştu.';
            }
        };
    } catch(e) {
        document.getElementById('aiTypingIndicator').style.display = 'none';
        aiDiv.style.color = '#ef4444';
        aiDiv.innerText = 'Bağlantı hatası: ' + e.message;
        body.scrollTop = body.scrollHeight;
    }
}
'''

# Replace the old sendAiMessage function
if 'async function sendAiMessage() {' in html:
    html = re.sub(r'async function sendAiMessage\(\) \{.*?\n\}\n</script>', new_send_message + '</script>', html, flags=re.DOTALL)
    
with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
    
print("Dashboard HTML patched for EventSource streaming.")
