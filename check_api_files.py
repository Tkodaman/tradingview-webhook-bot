import glob
for file in glob.glob("api/*.py"):
    with open(file, 'r', encoding='utf-8') as f:
        if '"/matrix"' in f.read() or "'/matrix'" in f.read():
            print(f"Found matrix route in {file}")
