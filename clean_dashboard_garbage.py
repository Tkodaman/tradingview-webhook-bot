import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Clean EPHEMERAL_MESSAGE blocks completely
pattern = r"The following is an <EPHEMERAL_MESSAGE>.*?</EPHEMERAL_MESSAGE>"
text = re.sub(pattern, "", text, flags=re.DOTALL)

# Clean bare EPHEMERAL_MESSAGE blocks
pattern2 = r"<EPHEMERAL_MESSAGE>.*?</EPHEMERAL_MESSAGE>"
text = re.sub(pattern2, "", text, flags=re.DOTALL)

# Clean json artifacts like ,"toolSummary":"..."}]}
pattern3 = r',\"toolSummary\":\"[^\"]*\"\}\]\}'
text = re.sub(pattern3, "", text)

# Clean random text like "tradingview-webhook-bot/templates/dashboard.html"
text = text.replace("tradingview-webhook-bot/templates/dashboard.html", "")

# Clean "d At: 2026-09-06T01:48:00+03:00" and "No results found"
pattern4 = r"d At: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+\d{2}:\d{2}"
text = re.sub(pattern4, "", text)
text = text.replace("No results found", "")
text = text.replace("Total occurrences: 4", "")
text = re.sub(r"--- At index \d+ ---", "", text)

# Ensure no empty style artifacts
text = re.sub(r'\n+', '\n', text)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Cleaned known garbage!")
