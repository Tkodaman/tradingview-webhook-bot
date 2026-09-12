with open('services/broker/alpaca_client.py', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace('\t', '    ')

with open('services/broker/alpaca_client.py', 'w', encoding='utf-8') as f:
    f.write(text)

import ast
try:
    ast.parse(text)
    print("Syntax OK")
except Exception as e:
    print(f"Error: {e}")
