with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Encode back to windows-1252/latin1 to get the raw bytes
try:
    raw_bytes = text.encode('windows-1254') # Turkish Windows
    fixed_text = raw_bytes.decode('utf-8')
    with open(r'templates\dashboard.html', 'w', encoding='utf-8') as f:
        f.write(fixed_text)
    print("Fixed using windows-1254!")
except Exception as e:
    print('Failed 1254:', e)
    
    try:
        raw_bytes = text.encode('windows-1252') # Western Windows
        fixed_text = raw_bytes.decode('utf-8')
        with open(r'templates\dashboard.html', 'w', encoding='utf-8') as f:
            f.write(fixed_text)
        print("Fixed using windows-1252!")
    except Exception as e:
        print('Failed 1252:', e)

