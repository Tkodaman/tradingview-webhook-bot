with open('services/order_router.py', 'r', encoding='utf-8') as f:
    text = f.read()
import re
text = re.sub(
    r'from services\.broker\.factory import get_broker\s*# PAPER modunda',
    '# PAPER modunda',
    text,
    flags=re.DOTALL
)
with open('services/order_router.py', 'w', encoding='utf-8') as f:
    f.write(text)
