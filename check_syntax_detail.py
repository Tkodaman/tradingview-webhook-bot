with open('services/broker/alpaca_client.py', 'r', encoding='utf-8') as f:
    text = f.read()
import ast
try:
    ast.parse(text)
except SyntaxError as e:
    print(f"Error at line {e.lineno}, text: {repr(e.text)}")
