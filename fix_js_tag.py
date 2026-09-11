with open('templates/cand_5b4e9.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re

# Find where the JS logic starts.
# It usually starts right after a </div> near line 1058.
# The exact text is:
#         // ================================================================
#         // 🕰️ CANLI SAAT VE PİYASA DURUMU

idx = text.find('// 🕰️ CANLI SAAT VE PİYASA DURUMU')
# Go back to the previous blank line or // ======
insert_idx = text.rfind('// ================================================================', 0, idx)
if insert_idx != -1:
    text = text[:insert_idx] + '<script>\n' + text[insert_idx:]
    print("Inserted <script> at index", insert_idx)

with open('templates/cand_5b4e9_fixed.html', 'w', encoding='utf-8') as f:
    f.write(text)
