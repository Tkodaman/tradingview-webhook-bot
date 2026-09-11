with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re
idx = text.find('MAIN CONTENT (Chart Removed)')
start_content = text.find('<div style="flex: 1 1 100%', idx)
end_content = text.find('</div>\n    <!-- END MAIN DASHBOARD GRID -->', start_content)
if end_content != -1:
    remaining_text = text[end_content:end_content+500]
    print(remaining_text)
