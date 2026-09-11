with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

idx_w_body = text.find('<body>')
idx_w_first_script = text.find('<script>', idx_w_body)
print("fetch inside JS code block?:", "fetch" in text[idx_w_first_script:])
