from html.parser import HTMLParser

class MyHTMLParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.tags = []
        self.errors = []
        
    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            self.tags.append((self.getpos(), attrs))
            
    def handle_endtag(self, tag):
        if tag == 'div':
            if len(self.tags) > 0:
                self.tags.pop()
            else:
                self.errors.append(self.getpos())

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()
    lines = text.split('\n')

parser = MyHTMLParser()
parser.feed(text)

if len(parser.errors) > 0:
    for pos in parser.errors:
        line_num = pos[0] - 1
        print(f"Extra closing div at line {pos[0]}:")
        print("...", lines[line_num-2])
        print("...", lines[line_num-1])
        print("->", lines[line_num])
        print("...", lines[line_num+1])
