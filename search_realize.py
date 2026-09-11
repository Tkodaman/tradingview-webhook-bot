import glob

for file in glob.glob("templates/*.html"):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            text = f.read()
        if 'REALİZE' in text:
            print("Found in:", file)
    except:
        pass
