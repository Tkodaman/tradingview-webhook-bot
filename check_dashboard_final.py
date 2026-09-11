with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
print("Has 15 Momentum:", "15 Momentum" in text)
print("Has Aktif:", "Aktif Açık" in text or "Aktif A" in text)
print("Has script:", "<script>" in text)
print("Number of body tags:", text.count("<body>"))
print("Number of script tags:", text.count("<script>"))
print("Number of html tags:", text.count("<html>"))
