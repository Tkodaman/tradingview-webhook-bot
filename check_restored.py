with open('dashboard_restored_from_chat.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
# check the first few lines to make sure it's valid HTML
print(text[:200])

# check length
print("Length:", len(text))
