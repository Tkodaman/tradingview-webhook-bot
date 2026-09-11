with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
style = re.findall(r'<style(.*?)</style>', text, flags=re.DOTALL)[0]
print("Lines in style:", len(style.split('\n')))
print("Length of style:", len(style))
