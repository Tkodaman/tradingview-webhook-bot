with open('templates/dashboard.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
# Find where the junk starts
idx_start = text.find('{"step_index":')
if idx_start != -1:
    # Find the end of the junk block
    # The junk is just transcript lines. The next valid HTML line is probably a CSS class or closing </style>
    # Let's print the start and end of the junk to see what we can safely remove.
    print(text[idx_start-100:idx_start+200])
