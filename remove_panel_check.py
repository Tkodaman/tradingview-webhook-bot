with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find('Algoritmik Hata')
if idx != -1:
    start_idx = text.rfind('<div class="panel"', 0, idx)
    end_idx_match = __import__('re').search(r'</div>\s*</div>\s*</div>\s*(?:<!--|$)', text[idx:])
    
    if start_idx != -1 and end_idx_match:
        end_idx = idx + end_idx_match.end()
        # Ensure we don't cut too much by finding the exact boundary. It's inside a main-grid probably.
        print("Found panel to remove, checking bounds...")
        print("Start:", start_idx, "End:", end_idx)
        print("Content to remove snippet:", text[start_idx:start_idx+100])
    else:
        print("Could not find start/end bounds cleanly.")
else:
    print("Could not find 'Algoritmik Hata' text.")
