with open('templates/cand_5b4e9.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

import re
print("Occurrences of <script>:", text.count('<script>'))
print("Occurrences of </script>:", text.count('</script>'))
