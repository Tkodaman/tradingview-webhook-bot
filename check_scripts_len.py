import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

scripts = re.findall(r'<script(.*?)</script>', text, flags=re.DOTALL)
print("Lengths of script tags:", [len(s) for s in scripts])
