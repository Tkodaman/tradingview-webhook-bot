with open('templates/dashboard_final.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Find the first script that is NOT the Chart.js src tag
idx_body = text.find('<body>')
idx_first_script_in_body = text.find('<script>', idx_body)
print("First script in body is at:", idx_first_script_in_body)
