with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

# Fix ws.onclose and close connectWebSocket
target = """            ws.onclose = () => {
                console.log("WebSocket Bağlantısı Koptu, Yeniden Bağlanılıyor...");
                document.querySelector('.live-dot').style.backgroundColor = 'var(--down-color)';
                setTimeout(connectWebSocket, 3000);
        }"""

replacement = """            ws.onclose = () => {
                console.log("WebSocket Bağlantısı Koptu, Yeniden Bağlanılıyor...");
                document.querySelector('.live-dot').style.backgroundColor = 'var(--down-color)';
                setTimeout(connectWebSocket, 3000);
            };
        } // End of connectWebSocket()"""

html = html.replace(target, replacement)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
