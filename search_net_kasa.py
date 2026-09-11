import glob

for file in glob.glob("templates/*.html"):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            text = f.read()
        if 'NET KASA' in text:
            print("Found in:", file)
    except:
        pass
