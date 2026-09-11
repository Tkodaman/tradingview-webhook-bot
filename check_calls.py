with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

print("Contains connectWebSocket(); call:", 'connectWebSocket();' in text)
print("Contains fetchPositions(); call:", 'fetchPositions();' in text)
