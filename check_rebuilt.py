with open('dashboard_rebuilt_properly.html', 'r', encoding='utf-8') as f:
    text = f.read()
print(len(text))
print("Lines:", len(text.splitlines()))
