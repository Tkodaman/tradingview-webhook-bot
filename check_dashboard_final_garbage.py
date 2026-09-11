with open('templates/dashboard_final.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

print("Contains EPHEMERAL_MESSAGE:", "EPHEMERAL_MESSAGE" in text)
