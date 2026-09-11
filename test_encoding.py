s = 'şğ'
# It was utf-8 bytes interpreted as latin1
try:
    s_bytes = s.encode('latin1')
    s_fixed = s_bytes.decode('utf-8')
    print('Fixed string:', s_fixed)
except Exception as e:
    print('Error:', e)
    
try:
    s_bytes = s.encode('cp1252')
    s_fixed = s_bytes.decode('utf-8')
    print('Fixed string (cp1252):', s_fixed)
except Exception as e:
    print('Error cp1252:', e)
