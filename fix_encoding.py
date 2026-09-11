with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's try to fix it using the ftfy library or just manual encoding/decoding
# In Windows, reading a UTF-8 file with cp1254 (Turkish) and then writing as UTF-16 might have caused this.
# The user's screenshot has şğ which means \xc5\x9f and \xc4\x9f were read as latin1 or cp1252.
# Let's try to reverse:
try:
    # First, let's get the raw bytes by encoding it back to cp1252
    raw_bytes = text.encode('cp1252', errors='ignore')
    fixed_text = raw_bytes.decode('utf-8', errors='ignore')
    
    with open('templates/dashboard_fixed.html', 'w', encoding='utf-8') as f:
        f.write(fixed_text)
        
    print("Fixed and saved to dashboard_fixed.html")
except Exception as e:
    print('Failed:', e)
