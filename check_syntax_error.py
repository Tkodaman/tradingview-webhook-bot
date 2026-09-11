with open('services/engine/experience_memory_engine.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

for i, line in enumerate(lines[350:370]):
    print(f"{350+i}: {line.rstrip()}")
