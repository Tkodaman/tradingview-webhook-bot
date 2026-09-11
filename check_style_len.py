with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
print("Length of style block:", len(re.findall(r'<style(.*?)</style>', text, flags=re.DOTALL)[0]))
