with open('_archive/dashboard_old.html', 'r', encoding='utf-16') as f:
    old = f.read()

with open('temp_sept3.html', 'r', encoding='utf-8') as f:
    sept3 = f.read()

print("Old lines:", len(old.splitlines()))
print("Sept 3 lines:", len(sept3.splitlines()))

# Print the first 50 lines of each to see the difference
print("--- Old ---")
print('\n'.join(old.splitlines()[:20]))
print("--- Sept 3 ---")
print('\n'.join(sept3.splitlines()[:20]))
