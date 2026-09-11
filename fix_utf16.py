import codecs

# Read raw bytes
with open(r'templates\dashboard.html', 'rb') as f:
    raw = f.read()

# Let's decode it as utf-16
try:
    text = raw.decode('utf-16')
    print("Decoded as utf-16 successfully!")
    with open(r'templates\dashboard.html', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Saved as utf-8!")
except Exception as e:
    print("Failed to decode utf-16:", e)
    
    # Maybe it is utf-16-le with BOM?
    try:
        text = raw.decode('utf-16-le')
        print("Decoded as utf-16-le successfully!")
        with open(r'templates\dashboard.html', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Saved as utf-8!")
    except Exception as e2:
        print("Failed utf-16-le:", e2)

