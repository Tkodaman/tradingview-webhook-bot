with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    lines = f.readlines()

print("--- TOP 30 LINES ---")
for line in lines[:30]:
    print(repr(line))

print("\n--- BOTTOM 30 LINES ---")
for line in lines[-30:]:
    print(repr(line))
