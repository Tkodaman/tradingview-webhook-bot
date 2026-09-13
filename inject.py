import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    content = f.read()

injection = """<script>
document.addEventListener("DOMContentLoaded", function() {
    // Clean old manual labels like (a6), (a1), [A1], [B2] etc.
    document.body.innerHTML = document.body.innerHTML.replace(/\\(a\\d+\\)/g, '').replace(/\\[[A-Z]\\d+\\]/g, '');

    const style = document.createElement('style');
    style.innerHTML = `
        .visual-tag {
            position: absolute;
            top: 6px;
            right: 6px;
            background: rgba(255, 215, 0, 0.2);
            color: #ffd700;
            border: 1px solid rgba(255, 215, 0, 0.5);
            padding: 2px 6px;
            border-radius: 4px;
            font-size: 10px;
            font-weight: bold;
            z-index: 999;
            pointer-events: none;
            backdrop-filter: blur(2px);
        }
        .panel, .kpi-card, .market-window {
            position: relative !important;
        }
    `;
    document.head.appendChild(style);

    let counter = 1;
    document.querySelectorAll('.panel').forEach((el) => {
        let tag = document.createElement('div');
        tag.className = 'visual-tag';
        tag.innerText = 'P' + counter++;
        el.appendChild(tag);
    });

    counter = 1;
    document.querySelectorAll('.market-window').forEach((el) => {
        let tag = document.createElement('div');
        tag.className = 'visual-tag';
        tag.innerText = 'W' + counter++;
        el.appendChild(tag);
    });

    counter = 1;
    document.querySelectorAll('.kpi-card').forEach((el) => {
        let tag = document.createElement('div');
        tag.className = 'visual-tag';
        tag.innerText = 'K' + counter++;
        el.appendChild(tag);
    });
});
</script>
</body>"""

# Remove any old injection if it exists
content = re.sub(r'<script>\s*document\.addEventListener\("DOMContentLoaded", function\(\) \{\s*// Clean old manual labels.*?</script>\s*</body>', '</body>', content, flags=re.DOTALL)

content = content.replace('</body>', injection)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(content)
