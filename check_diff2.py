with open('_archive/dashboard_old.html', 'r', encoding='utf-16', errors='ignore') as f:
    old = f.read()

with open('temp_sept3.html', 'r', encoding='utf-16', errors='ignore') as f:
    sept3 = f.read()

print("Old lines:", len(old.splitlines()))
print("Sept 3 lines:", len(sept3.splitlines()))

