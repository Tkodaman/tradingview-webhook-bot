import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Terminals scrollable
text = re.sub(r'(\.code-block\s*\{[^}]*)(\})', r'\1 max-height: 250px; overflow-y: auto; \2', text)

# 2. Make two-col-grid single column for full width
text = re.sub(r'\.two-col-grid\s*\{[^}]*grid-template-columns:\s*1fr\s+1fr;', r'.two-col-grid {\n            display: grid;\n            grid-template-columns: 1fr;', text)

# 3. Swap Top 15 and Aktif Pozisyonlar physically
idx_aktif = text.find('Aktif A')
idx_top15 = text.find('Top 15 Al')

if idx_aktif != -1 and idx_top15 != -1:
    aktif_start = text.rfind('<div class="panel"', 0, idx_aktif)
    
    # We need to find where Aktif ends. It ends just before the next <div class="panel"> or <div class="two-col-grid">
    aktif_end_match = re.search(r'<div class="(panel|two-col-grid|main-grid|future-panel)"', text[idx_aktif:])
    if aktif_end_match:
        aktif_end = idx_aktif + aktif_end_match.start()
    else:
        aktif_end = len(text)
        
    top15_start = text.rfind('<div style="background:linear-gradient', 0, idx_top15)
    
    # Top 15 ends before the next major section
    top15_end_match = re.search(r'<!--|(?:\n\s*<div class="(?:panel|two-col-grid|main-grid|future-panel)")', text[idx_top15:])
    if top15_end_match:
        top15_end = idx_top15 + top15_end_match.start()
    else:
        top15_end = len(text)

    # Let's write a safer physical swap script if they are in the wrong order.
    if top15_start > aktif_end:
        print("Top 15 is after Aktif. Swapping...")
        aktif_html = text[aktif_start:aktif_end]
        top15_html = text[top15_start:top15_end]
        
        # Remove from original
        text = text[:aktif_start] + text[aktif_end:top15_start] + text[top15_end:]
        # Now insert top15 first, then aktif
        text = text[:aktif_start] + top15_html + "\n" + aktif_html + text[aktif_start:]
    elif aktif_start > top15_end:
        print("Top 15 is already before Aktif. No swap needed.")
    else:
        print("Overlap or parsing issue, cannot swap.")
else:
    print("Could not find both panels.")

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)
print("Updated dashboard with scrollable terminals and verified panel order.")
