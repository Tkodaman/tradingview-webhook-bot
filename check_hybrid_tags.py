with open('templates/dashboard_hybrid.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
print("Num <script>:", text.count('<script>'))
print("Num </script>:", text.count('</script>'))
