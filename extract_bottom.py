import re
with open('templates/dashboard_working_backup.html', 'r', encoding='utf-8') as f:
    text = f.read()

# We need the HTML div that contains the active positions and history
# They are usually <div class="panel"> elements.
# Let's extract the whole block starting from the active positions panel.

idx_start = text.find('<div class="panel">', 29000)
# we want to extract everything until the end of the body content.
# Usually this ends before the <script> tag starts.
idx_end = text.find('<script>', idx_start)

extracted_html = text[idx_start:idx_end]

with open('templates/bottom_half.html', 'w', encoding='utf-8') as f:
    f.write(extracted_html)

print(f"Extracted bottom HTML. Length: {len(extracted_html)}")
