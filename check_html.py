from html.parser import HTMLParser

class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.errors = []
        
    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            self.tags.append(tag)
            
    def handle_endtag(self, tag):
        if tag == 'div':
            if len(self.tags) > 0:
                self.tags.pop()
            else:
                self.errors.append("Extra closing div found")

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

parser = MyHTMLParser()
parser.feed(text)

print(f"Unclosed div tags count: {len(parser.tags)}")
print(f"Extra closing div tags count: {len(parser.errors)}")
