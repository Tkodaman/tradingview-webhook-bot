with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('<EPHEMERAL_MESSAGE>')
print("Text length:", len(text))
print("Ephemeral starts at:", idx)

# Let's see what is after the ephemeral message
end_idx = text.find('</EPHEMERAL_MESSAGE>') + len('</EPHEMERAL_MESSAGE>')
if end_idx != -1:
    print("Characters after ephemeral message:", len(text) - end_idx)
