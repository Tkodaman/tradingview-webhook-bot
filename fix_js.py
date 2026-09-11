with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

import re

# We want to restore the updatePnlChart function cleanly.
# Find where updatePnlChart is supposed to be.

old_code = r'''            const labels = history.map((item, idx) => {
                if (typeof item === 'object' && item.time) return item.time;
                return idx === 0 ? 'Start' : 'İşlem #' + idx;
            });
            const data = history.map(item => typeof item === 'object' ? parseFloat(item.value) : parseFloat(item));'''

new_code = r'''        function updatePnlChart(history) {
            if (!pnlChart || !history || history.length === 0) return;
            
            const labels = history.map((item, idx) => {
                if (typeof item === 'object' && item.time) return item.time;
                return idx === 0 ? 'Start' : 'İşlem #' + idx;
            });
            const data = history.map(item => typeof item === 'object' ? parseFloat(item.value) : parseFloat(item));'''

text = text.replace(old_code, new_code)

with open(r'templates\dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Fixed updatePnlChart syntax error cleanly.")
