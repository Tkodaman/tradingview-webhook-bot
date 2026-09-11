import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# Let's find the first ephemeral message
idx = text.find('<EPHEMERAL_MESSAGE>')
print("First ephemeral at:", idx)

# Let's print 500 characters around it to see what the garbage is
import sys
sys.stdout.buffer.write(text[max(0, idx-200):idx+500].encode('utf-8'))
