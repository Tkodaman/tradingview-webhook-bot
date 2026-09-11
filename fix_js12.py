import re
with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace ANY instance of `balEl.innerText = ${parseFloat...` with backticks
text = re.sub(r'balEl\.innerText = \$\{parseFloat\((.*?)\)\.toFixed\(2\)\};', r'balEl.innerText = `$$${parseFloat(\1).toFixed(2)}`;', text)
text = re.sub(r'if \(ce\) ce\.innerText = \$\{parseFloat\((.*?)\)\.toFixed\(2\)\};', r'if (ce) ce.innerText = `$$${parseFloat(\1).toFixed(2)}`;', text)

with open(r'templates\dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Replaced with regex!")
