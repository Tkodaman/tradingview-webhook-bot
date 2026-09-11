import re

with open('templates/cand_perfect2.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx_last_script = text.rfind('<script')
print("Last <script at:", idx_last_script)

html_part = text[:idx_last_script]
print("HTML length before last script:", len(html_part))

with open('final_clean_html_body_only.html', 'w', encoding='utf-8') as f:
    f.write(html_part)
