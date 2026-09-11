import re

with open('templates/cand_perfect_fixed.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx_last_script_start = text.rfind('<script>')
html_body = text[:idx_last_script_start]

print("HTML Body length:", len(html_body))

with open('final_clean_html_body.txt', 'w', encoding='utf-8') as f:
    f.write(html_body)
