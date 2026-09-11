import os
for f in os.listdir('.'):
    if f.endswith('.js') or f.endswith('.py'):
        with open(f, 'r', encoding='utf-8', errors='ignore') as file:
            text = file.read()
            if 'FUTURE_STREAM_POOL' in text:
                print(f"Found in {f}")
