import glob
import os

for f in glob.glob('templates/cand_*.html'):
    with open(f, 'r', encoding='utf-8', errors='ignore') as file:
        content = file.read()
        lines = len(content.splitlines())
        has_kripto = 'Kripto Piyasası' in content
        print(f"{os.path.basename(f)}: size {len(content)}, lines {lines}, Kripto: {has_kripto}")
