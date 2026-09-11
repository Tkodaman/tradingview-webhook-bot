with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    js = f.read()

print("Islem fix applied:", "'Islem #' + idx;" in js)
print("balEl fix applied:", "balEl.innerText = $" in js)
