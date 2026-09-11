import re
with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()
    
# Let's find out if there's any logic to render the table rows.
# Look for 'activePositionsBody' or similar
if 'activePositionsBody' in text:
    print("Found activePositionsBody in HTML.")
    
# check if fetchPositions is there
if 'fetchPositions' in text:
    print("Found fetchPositions.")
