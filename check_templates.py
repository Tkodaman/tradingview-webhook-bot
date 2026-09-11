import glob
for f in glob.glob('templates/*.html'):
    with open(f, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.read()
        if 'Kripto Piyasası' in content or 'momentum hedef listesi' in content or 'Güven:' in content:
            print("FOUND IN:", f)
            print("Size:", len(content))
