with open('services/broker/alpaca_client.py', 'r', encoding='utf-8') as f:
    text = f.read()

# Try converting all tabs to 4 spaces
text = text.replace('\t', '    ')

import ast
try:
    ast.parse(text)
    print("Syntax OK after tab replace")
    with open('services/broker/alpaca_client.py', 'w', encoding='utf-8') as f:
        f.write(text)
except Exception as e:
    print(f"Error: {e}")
