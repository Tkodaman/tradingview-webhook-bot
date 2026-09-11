with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
idx = text.find('MAIN CONTENT (Chart Removed)')
start = text.find('<div style="flex: 1 1 100%', idx)

# Print up to the first panel
end = text.find('Top 15 Al', start)
print(re.sub(r'[^\x00-\x7F]+', ' ', text[start:end+50]))
