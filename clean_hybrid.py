with open('templates/dashboard_hybrid.html', 'r', encoding='utf-8', errors='ignore') as f:
    text = f.read()

# The junk starts at {"step_index": (idx 32948)
idx_start = text.find('{"step_index":')

if idx_start != -1:
    # Let's find where the junk ends. 
    # It probably ends right before         /* 2-COLUMN GRID (RULES & SUMMARY) */
    # Or right before .inner-box {
    idx_end1 = text.find('        /* 2-COLUMN GRID (RULES & SUMMARY) */', idx_start)
    idx_end2 = text.find('        .stat-grid {', idx_start)
    
    idx_end = idx_end1 if idx_end1 != -1 else idx_end2
    
    if idx_end == -1:
        # Just find the next occurrence of a CSS class         .
        import re
        match = re.search(r'(\n\s*\.[a-zA-Z0-9_-]+\s*\{)', text[idx_start:])
        if match:
            idx_end = idx_start + match.start()
        
    print(f"Junk start: {idx_start}, Junk end: {idx_end}")
    print("End context:")
    print(text[idx_end:idx_end+200])
    
    clean_text = text[:idx_start] + text[idx_end:]
    
    # Check if there is ANY OTHER junk!
    idx_start2 = clean_text.find('{"step_index":')
    print("Is there a second chunk of junk?", idx_start2)
    
    with open('templates/dashboard_hybrid_clean.html', 'w', encoding='utf-8') as f:
        f.write(clean_text)
    print("Saved clean hybrid!")
else:
    print("No junk found?!")
