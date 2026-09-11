import os
print(f"{'Filename':<30} | {'Size':<10} | {'Top 15':<8} | {'panel-container':<16} | {'Aktif A':<8}")
for f in os.listdir('templates'):
    if f.endswith('.html'):
        path = os.path.join('templates', f)
        size = os.path.getsize(path)
        with open(path, 'r', encoding='utf-8', errors='ignore') as file:
            text = file.read()
            has_top15 = 'Top 15' in text
            has_panel = 'panel-container' in text
            has_aktif = 'Aktif A' in text
            print(f"{f:<30} | {size:<10} | {str(has_top15):<8} | {str(has_panel):<16} | {str(has_aktif):<8}")
