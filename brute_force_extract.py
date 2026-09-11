import json
import glob
import os
import re

brain_dir = r'C:\Users\ASUS\.gemini\antigravity-ide\brain'
files = glob.glob(os.path.join(brain_dir, '*', '.system_generated', 'logs', '*full.jsonl'))

all_text = ""
for f in files:
    try:
        with open(f, 'r', encoding='utf-8') as file:
            all_text += file.read()
    except Exception as e:
        pass

# Decode ALL json strings? No, the text in the file is already a JSON dump.
# The html code will have \n and \" escaping inside the JSON strings.
# But wait, the jsonl could have been pretty printed? No, it's one line per JSON.

# Let's find all occurrences of "<!DOCTYPE html>" up to "</html>"
# Note that they are escaped like <!DOCTYPE html>\\n<html
pattern = r'<!DOCTYPE html>.*?</html>'
matches = re.findall(pattern, all_text, re.DOTALL)

print("Found", len(matches), "matches")

valid_matches = []
for m in matches:
    # Check if this is the TRADINGVIEW one
    if 'TRADINGVIEW' in m or 'TradingView' in m or 'TRADINGVIEW' in m.replace('\\n', ''):
        valid_matches.append(m)

print("Valid TradingView matches:", len(valid_matches))

if valid_matches:
    # Sort by length, assuming the longest is the most complete dashboard
    valid_matches.sort(key=lambda x: len(x))
    best = valid_matches[-1]
    print("Longest match length:", len(best))
    
    # decode escapes
    best = best.replace('\\n', '\n').replace('\\t', '\t').replace('\\"', '"').replace('\\\\', '\\')
    
    with open('templates/dashboard_restored.html', 'w', encoding='utf-8') as out:
        out.write(best)
    print("Saved to templates/dashboard_restored.html")

