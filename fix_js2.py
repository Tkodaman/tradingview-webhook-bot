with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

old_block = '''                if (balEl && data.account_balance !== undefined) {
                    lastAlpacaBalance = parseFloat(data.account_balance);
                    balEl.innerText = $
                    const ce = document.getElementById('chartLatestEquity');
                    if (ce) ce.innerText = $;
                };
                }'''

new_block = '''                if (balEl && data.account_balance !== undefined) {
                    lastAlpacaBalance = parseFloat(data.account_balance);
                    balEl.innerText = $;
                    const ce = document.getElementById('chartLatestEquity');
                    if (ce) ce.innerText = $;
                }'''

# Replace exactly
if old_block in text:
    text = text.replace(old_block, new_block)
    with open(r'templates\dashboard.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Replaced successfully!")
else:
    print("Could not find the block! The block might have some hidden characters or slightly different whitespace.")
