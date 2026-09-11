with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

def search(query):
    for i, line in enumerate(lines):
        if query in line:
            print(f"{i+1}: {line.strip()}")

print('--- Clock ---')
search('Hafta')
print('--- Fetch Positions ---')
search('fetchPositions')
print('--- Risk Modes ---')
search('risk-modes-bar')
