from bs4 import BeautifulSoup
import sys

with open(r'_archive\dashboard_old.html', 'r', encoding='utf-16') as f:
    text = f.read()

soup = BeautifulSoup(text, 'html.parser')

print("Unclosed tags or issues:")
# Beautiful Soup automatically fixes tags, so let's just see if the body is intact.
body = soup.find('body')
if body:
    print("Body length:", len(str(body)))
else:
    print("NO BODY FOUND!")
