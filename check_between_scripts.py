with open('templates/dashboard_final.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

print("HTML between Script 1 and 3:")
print(text[142583:142583+500].encode('ascii', 'ignore').decode('ascii'))
