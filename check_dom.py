with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

print("Has DOMContentLoaded:", 'DOMContentLoaded' in text)
print("Has fetchLiveMatrix call:", 'fetchLiveMatrix();' in text)
