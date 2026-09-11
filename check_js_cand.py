import re

with open('templates/cand_perfect_fixed.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

scripts = text.split('<script>')
print(f"Number of <script> tags: {len(scripts)-1}")

idx_first_script = text.find('<script>')
idx_last_script = text.rfind('</script>')
print("Text length:", len(text))
print("First <script> at:", idx_first_script)
print("Last </script> at:", idx_last_script)

# Remove all scripts
if idx_first_script != -1 and idx_last_script != -1:
    no_js = text[:idx_first_script] + text[idx_last_script+9:]
    print("HTML length without JS:", len(no_js))
