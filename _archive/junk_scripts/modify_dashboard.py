with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

# 1. Terminal Scroll
# Look for .code-block CSS
import re
text = re.sub(r'(\.code-block\s*\{[^}]*)(\})', r'\1 max-height: 250px; overflow-y: auto; \2', text)

# 2. Make Top 15 Full Width
# Find the Top 15 container and its parent. If parent is grid, make it span full width or change layout.
# Look for <div class="two-col-grid"> that wraps Top 15, or maybe it's something else.
# Instead of guessing, let's inject a global CSS rule for the specific panels if possible.
# Actually, the Top 15 is <div style="background:linear-gradient... ">
# And Aktif is <div class="panel">

# Let's completely separate them and put them at the very root of <div class="main-grid"> if they aren't.
# Currently:
# <div class="main-grid">
#    <div class="panel"> ... (Left column?)
#    <div class="panel"> ... (Right column?)
# </div>

# Let's extract Top15 and Aktif, and place them at the very top of .main-grid, wrapping them in a full-width container.
idx_top15 = text.find('Top 15 Al')
top15_start = text.rfind('<div style="background:linear-gradient', 0, idx_top15)

# Wait, Top 15 might contain child divs that close.
# A simple way to make them full width is to change their parent grid.
# If .main-grid is grid-template-columns: 2fr 1fr; or something, we can override it!
