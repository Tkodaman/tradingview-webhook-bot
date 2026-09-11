import sys

def fix_file():
    try:
        with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
            text = f.read()
            
        replacements = {
            '\u00c5\u0178': '\u015f',
            '\u00c4\u0178': '\u011f',
            '\u00c4\u00b1': '\u0131',
            '\u00c3\u00a7': '\u00e7',
            '\u00c3\u00b6': '\u00f6',
            '\u00c3\u00bc': '\u00fc',
            '\u00c5\u017e': '\u015e',
            '\u00c4\u017e': '\u011e',
            '\u00c4\u00b0': '\u0130',
            '\u00c3\u2021': '\u00c7',
            '\u00c3\u2013': '\u00d6',
            '\u00c3\u0153': '\u00dc',
            '??': '\u00dc',
            '??': '\u00d6',
            '??': '\u00c7',
            '??': '\u0130',
            '??': '\u011e',
            '??': '\u015e',
            '??': '\u00fc',
            '??': '\u00f6',
            '??': '\u00e7',
            '??': '\u0131',
            '??': '\u011f',
            '??': '\u015f',
            '??': '?',
            '??': '?',
            '??': '?',
            '??': '?',
            '??': '?',
            '??': '?'
        }
        
        for k, v in replacements.items():
            text = text.replace(k, v)
            
        with open(r'templates\dashboard.html', 'w', encoding='utf-8') as f:
            f.write(text)
        print("Success")
    except Exception as e:
        print("Error:", e)

fix_file()
