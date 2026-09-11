from html.parser import HTMLParser

class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        
    def handle_starttag(self, tag, attrs):
        if tag not in ['meta', 'link', 'br', 'hr', 'img', 'input', 'source']:
            self.tags.append(tag)
            
    def handle_endtag(self, tag):
        if tag not in ['meta', 'link', 'br', 'hr', 'img', 'input', 'source']:
            if self.tags and self.tags[-1] == tag:
                self.tags.pop()
            else:
                pass # print("Mismatch")

parser = MyHTMLParser()
with open(r'templates\cand_22e24.html_clean.html', 'r', encoding='utf-8') as f:
    html = f.read()
    
# Did we successfully get an </html>?
if '</html>' in html:
    print("Has </html>")
else:
    print("MISSING </html>")

print("Size:", len(html))

parser.feed(html)
print("Remaining open tags:", parser.tags)
