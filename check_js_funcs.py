with open('pure_js_clean.js', 'r', encoding='utf-8') as f:
    js = f.read()

functions_to_check = [
    'exportCsvData',
    'openJsonModal',
    'openPerformanceModal',
    'openMultiplierModal',
    'calibrateEngine',
    'setRiskMode',
    'resetEquity'
]

for fn in functions_to_check:
    if fn in js:
        print(f"{fn} is in JS!")
    else:
        print(f"{fn} is MISSING from JS!")
