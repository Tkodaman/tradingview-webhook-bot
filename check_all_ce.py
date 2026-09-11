import glob

for file in glob.glob("templates/*.html"):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        for i, line in enumerate(lines):
            if 'ce.innerText' in line:
                print(f"{file} Line {i+1}: {line.strip()}")
                break
    except:
        pass
