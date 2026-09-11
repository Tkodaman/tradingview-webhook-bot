with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("balEl.innerText = ;", "balEl.innerText = ${parseFloat(data.account_balance).toFixed(2)};")
text = text.replace("if (ce) ce.innerText = ;", "if (ce) ce.innerText = ${parseFloat(data.account_balance).toFixed(2)};")

text = text.replace("balEl.innerText = $;", "balEl.innerText = ${parseFloat(summary.account_balance).toFixed(2)};")

with open(r'templates\dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Fixed!")
