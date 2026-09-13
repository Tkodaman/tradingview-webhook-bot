import os

html_path = 'templates/dashboard.html'
with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

import re
old_input = r'<input type="range" id="capitalSlider" min="5" max="50" step="5" value="{{ settings\.dynamic_capital_allocation_pct }}" \s*onchange="setCapitalAllocation\(this\.value\)"\s*oninput="document\.getElementById\(\'capitalValue\'\)\.innerText = \'%\' \+ this\.value \+ \' \(\$\' \+ Math\.round\(this\.value \* \{\{ settings\.base_portfolio_size \}\} / 100\) \+ \'\)\'"\s*style="flex: 1; cursor: pointer; accent-color: #3b82f6;">'
new_input = '''<input type="range" id="capitalSlider" min="5" max="100" step="5" value="{{ settings.dynamic_capital_allocation_pct }}" 
                         onchange="setCapitalAllocation(this.value)"
                         oninput="let bal = (typeof lastAlpacaBalance !== 'undefined' && lastAlpacaBalance > 0) ? lastAlpacaBalance : {{ settings.base_portfolio_size }}; document.getElementById('capitalValue').innerText = '%' + this.value + ' ($' + Math.round(this.value * bal / 100) + ')';"
                         style="flex: 1; cursor: pointer; accent-color: #3b82f6;">'''

content = re.sub(old_input, new_input, content, count=1)

with open(html_path, 'w', encoding='utf-8') as f:
    f.write(content)

runner_path = 'services/engine/auto_runner.py'
with open(runner_path, 'r', encoding='utf-8') as f:
    runner_content = f.read()

runner_content = runner_content.replace('required_score = 6\n                min_vol = 0.5', 'required_score = 5\n                min_vol = 0.3')
runner_content = runner_content.replace('required_score = 7\n                min_vol = 1.0', 'required_score = 6\n                min_vol = 0.7')
runner_content = runner_content.replace('required_score = 8\n                min_vol = 1.2', 'required_score = 7\n                min_vol = 1.0')
runner_content = runner_content.replace('required_score = 9\n                min_vol = 1.5', 'required_score = 8\n                min_vol = 1.2')

with open(runner_path, 'w', encoding='utf-8') as f:
    f.write(runner_content)

print('Success')
