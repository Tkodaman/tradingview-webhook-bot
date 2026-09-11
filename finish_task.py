with open('C:\\Users\\ASUS\\.gemini\\antigravity-ide\\brain\\456e22e9-0bf5-47c3-a3df-2e9c6bdf32ff\\task.md', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('[/] Update 	emplates/dashboard.html to add HTML', '[x] Update 	emplates/dashboard.html to add HTML')
text = text.replace('[ ] Update 	emplates/dashboard.html JavaScript to poll/sync', '[x] Update 	emplates/dashboard.html JavaScript to poll/sync')
text = text.replace('[ ] Update 	emplates/dashboard.html JavaScript to implement', '[x] Update 	emplates/dashboard.html JavaScript to implement')

with open('C:\\Users\\ASUS\\.gemini\\antigravity-ide\\brain\\456e22e9-0bf5-47c3-a3df-2e9c6bdf32ff\\task.md', 'w', encoding='utf-8') as f:
    f.write(text)
