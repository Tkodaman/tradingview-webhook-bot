import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Fix the İşlem # syntax error
text = re.sub(r"return idx === 0 \? 'Start' : [^;]+;", "return idx === 0 ? 'Start' : İşlem #;", text)

# Fix the Ephemeral message and truncation
idx_eph = text.find('<EPHEMERAL_MESSAGE>')
if idx_eph != -1:
    # the truncation happened in else if (item.icon === '🟡') borderColor = 'rgba
    # Let's find orderColor = 'rgba just before the ephemeral message
    idx_rgba = text.rfind("borderColor = 'rgba", 0, idx_eph)
    if idx_rgba != -1:
        # replace from idx_rgba to the end of the script with the proper closure
        # wait, the original function enderTradeHistory was in ottom_js.
        # Since I'm cutting off here, I need to close the enderTradeHistory function, and maybe connectWebSocket?
        # Actually, let's just close the block.
        # Wait, the exact original cand_perfect2 JS ended abruptly there!
        pass

# Let's just remove the Ephemeral message and the </EPHEMERAL_MESSAGE>
text = re.sub(r'<EPHEMERAL_MESSAGE>.*?</EPHEMERAL_MESSAGE>', '', text, flags=re.DOTALL)
text = re.sub(r'<EPHEMERAL_MESSAGE>.*', '}\n}\n</script>\n</body>\n</html>', text, flags=re.DOTALL)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("CLEANSED HTML 2!")
