with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

count = 0
while True:
    idx1 = text.find('The following is an <EPHEMERAL_MESSAGE>')
    if idx1 == -1:
        # Check for plain EPHEMERAL_MESSAGE
        idx1 = text.find('<EPHEMERAL_MESSAGE>')
        if idx1 == -1:
            break
            
    idx2 = text.find('</EPHEMERAL_MESSAGE>', idx1)
    if idx2 == -1:
        break
        
    text = text[:idx1] + text[idx2 + len('</EPHEMERAL_MESSAGE>'):]
    count += 1

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print(f"Removed {count} ephemeral blocks using index slicing.")
