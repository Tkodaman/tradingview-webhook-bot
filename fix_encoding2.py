# -*- coding: utf-8 -*-
with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

encodings_to_try = ['cp1254', 'iso-8859-9', 'iso-8859-1', 'cp1252', 'latin1']

for enc in encodings_to_try:
    try:
        raw_bytes = text.encode(enc)
        fixed_text = raw_bytes.decode('utf-8')
        if 'P\u0130YASA' in fixed_text:
            print(f'SUCCESS with {enc}')
            with open('templates/dashboard.html', 'w', encoding='utf-8') as f2:
                f2.write(fixed_text)
            break
    except Exception as e:
        pass
else:
    print('None worked perfectly without errors.')
