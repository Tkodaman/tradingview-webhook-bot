with open('final_clean_html_body.txt', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

print(text[-1500:])
