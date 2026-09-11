with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
# Check where the valid HTML ends or begins
idx1 = text.find('</style>')
idx2 = text.find('{"step_index"')
print("</style> at", idx1)
print("json starts at", idx2)
