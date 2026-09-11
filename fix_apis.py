import re

with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Replace /api/account/reset with /api/positions/reset-account
text = text.replace('/api/account/reset', '/api/positions/reset-account')

# Ensure WebSocket URL is correct
if 'wsUrl = ws:///ws/live;' in text:
    text = text.replace('wsUrl = ws:///ws/live;', 'wsUrl = ws:///live;')

# Wait, earlier I did html.replace('/ws/live', '/live'), which might have replaced ws:///live which is fine.

with open(r'templates\dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Replaced API endpoints in dashboard.html.")
