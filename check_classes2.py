with open('templates/cand_perfect_fixed.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx = text.find('Top 15 Al')
import re
print(re.sub(r'[^\x00-\x7F]+', ' ', text[idx-200:idx+100]))
