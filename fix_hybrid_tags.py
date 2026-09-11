with open('templates/dashboard_hybrid.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# Let's just find where the massive javascript starts in the body and prepend <script> if it's missing.
# Line 1060 or so in cand_5b4e9.html has const AYLAR = ....
idx = text.find('const AYLAR = [')
if idx != -1:
    # go back to find the closest <script> tag before this
    prev_script = text.rfind('<script>', 0, idx)
    prev_end_script = text.rfind('</script>', 0, idx)
    if prev_end_script > prev_script or prev_script == -1:
        # There is no open script tag here! We must insert one!
        # find the start of this script block, probably after </div>\r\n
        # Let's just find const AYLAR and go back to     // =====================================
        start_js = text.rfind('    // ================================================================', 0, idx)
        if start_js != -1:
            text = text[:start_js] + '<script>\n' + text[start_js:]
            print("Inserted missing <script> tag!")

with open('templates/dashboard_hybrid.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Num <script>:", text.count('<script>'))
print("Num </script>:", text.count('</script>'))
