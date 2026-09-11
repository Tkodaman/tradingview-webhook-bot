import re

with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx_body = text.find('<body>')
idx_script_start = text.find('<script>', idx_body)
idx_script_end = text.find('</script>', idx_script_start)

pure_js = text[idx_script_start+8:idx_script_end]

# Fix the Islem error
pure_js = re.sub(r"return idx === 0 \? 'Start' : .*?;", "return idx === 0 ? 'Start' : 'Islem #' + idx;", pure_js)

# Fix balEl syntax error line 1
if "balEl.innerText = `$${parseFloat(data.account_balance).toFixed(2)\n" in pure_js:
    pure_js = pure_js.replace("balEl.innerText = `$${parseFloat(data.account_balance).toFixed(2)\n", "balEl.innerText = `$${parseFloat(data.account_balance).toFixed(2)}`;\n")

# Fix balEl syntax error line 2
if "balEl.innerText = `$${parseFloat(summary.account_balance).toFixed(2)}\n" in pure_js:
    pure_js = pure_js.replace("balEl.innerText = `$${parseFloat(summary.account_balance).toFixed(2)}\n", "balEl.innerText = `$${parseFloat(summary.account_balance).toFixed(2)}`;\n")


with open('pure_js_clean.js', 'w', encoding='utf-8') as f:
    f.write(pure_js)

print("Saved pure_js_clean.js, length:", len(pure_js))
