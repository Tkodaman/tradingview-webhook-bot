with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

text = text.replace("return idx === 0 ? 'Start' : Islem #;", "return idx === 0 ? 'Start' : 'Islem #' + idx;")
text = text.replace("return idx === 0 ? 'Start' : İşlem #;", "return idx === 0 ? 'Start' : 'Islem #' + idx;")

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Fixed backticks!")
