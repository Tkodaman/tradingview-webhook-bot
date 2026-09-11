with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Close the wallet-bar right after wallet-info
# Find wallet-info end
idx_info = text.find('class="wallet-info"')
idx_info_end = text.find('</div>', idx_info) + 6

# Insert </div> to close wallet-bar
text = text[:idx_info_end] + '\n    </div>\n' + text[idx_info_end:]

# 2. Let's find the filter-tabs and move it back into wallet-bar
# Wait, if we move it back into wallet-bar, we have to find it first.
idx_filter_start = text.find('<div style="display: flex; gap: 8px; align-items: center; flex-wrap: wrap;">\n            <div class="filter-tabs">')
if idx_filter_start != -1:
    idx_filter_end = text.find('</button>\n        </div>', idx_filter_start) + 24
    filter_html = text[idx_filter_start:idx_filter_end]
    
    # Remove from original
    text = text[:idx_filter_start] + text[idx_filter_end:]
    
    # Put it back into wallet-bar
    idx_wallet_close = text.find('\n    </div>\n    <!-- MOVED AKTIF POZISYONLAR -->')
    text = text[:idx_wallet_close] + '\n        ' + filter_html + text[idx_wallet_close:]
else:
    print("Filter tabs not found")

with open('templates/dashboard_fixed.html', 'w', encoding='utf-8') as f:
    f.write(text)
print("Fixed wallet-bar and filter-tabs")
