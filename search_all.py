import os
import glob

for ext in ('*.py', '*.html', '*.js'):
    for path in glob.glob('**/' + ext, recursive=True):
        if 'venv' in path or 'node_modules' in path: continue
        try:
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
                if 'Güven' in content or 'Kripto Piyasası' in content or 'RSI:' in content:
                    print("Found in", path)
        except Exception:
            pass
