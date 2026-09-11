with open('templates/dashboard_found.html', 'r', encoding='utf-8') as f:
    html = f.read()
    
print("Length:", len(html))
print("First 300 chars:")
print(html[:300])
