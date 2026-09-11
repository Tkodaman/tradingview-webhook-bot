with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
# Let's fix the truncated JS at the very end.
# I'll just find the exact text and replace it with closed brackets.
old_tail = '''            } catch (err) {
                showToast("Sunucuya bağlanılamadı!", "error");
            } finally {
                btn.innerText = "🚀 Tetikle";
                btn.disabled = false;
            }
        }
    </script>'''

# Let's see if we can just re-parse the JS and append closing brackets until it balances.
js_match = re.search(r'<script>(.*)</script>', text, re.DOTALL)
if js_match:
    js_code = js_match.group(1)
    opens = js_code.count('{')
    closes = js_code.count('}')
    diff = opens - closes
    
    if diff > 0:
        # append the closing brackets BEFORE the </script> tag!
        idx_script_end = text.rfind('</script>')
        text = text[:idx_script_end] + ('}\n' * diff) + text[idx_script_end:]
        print(f"Appended {diff} closing brackets!")
        
with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)
