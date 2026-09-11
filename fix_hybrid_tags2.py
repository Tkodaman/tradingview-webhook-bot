with open('templates/dashboard_hybrid.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re

# Find the end of the HTML body. Usually the massive script is right before </body>
idx = text.rfind('</body>')
if idx != -1:
    # Just to be super safe, I'll replace ALL <script> and </script> tags in the body with nothing,
    # except the ones in the <head>, and then wrap the whole JS block in ONE <script> tag.
    pass

# Actually, let's just see where the 3 </script> are.
scripts_close = [m.start() for m in re.finditer(r'</script>', text)]
scripts_open = [m.start() for m in re.finditer(r'<script', text)]
print("Open:", scripts_open)
print("Close:", scripts_close)
