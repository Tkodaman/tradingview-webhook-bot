import re

with open('templates/dashboard.html', 'r', encoding='utf-8') as f:
    html = f.read()

ugly_block_regex = r'\\n\s*<!-- TOKEN TRACKER WIDGET -->.*?</div>\s*</div>\s*</div>'
# The token widget has 3 closing divs.
# Let's just find exactly what I injected earlier.
token_widget_code = r'''\n                  <!-- TOKEN TRACKER WIDGET -->
                  <div style="background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 8px; padding: 6px 12px; display: flex; flex-direction: column; align-items: flex-end;">
                      <div style="font-size: 11px; color: #a78bfa; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">LLM Token Limit</div>
                      <div style="display: flex; align-items: center; gap: 8px;">
                          <div style="width: 60px; height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; overflow: hidden;">
                              <div id="tokenProgressBar" style="width: 100%; height: 100%; background: #10b981; transition: width 0.3s, background 0.3s;"></div>
                          </div>
                          <span id="tokenCounter" style="font-family: 'JetBrains Mono', monospace; font-size: 14px; font-weight: 700; color: #fff;">1,000,000</span>
                      </div>
                  </div>'''

html = html.replace(token_widget_code, "")

new_token_widget = '''                  <!-- TOKEN TRACKER WIDGET -->
                  <div style="background: rgba(139, 92, 246, 0.1); border: 1px solid rgba(139, 92, 246, 0.3); border-radius: 8px; padding: 4px 10px; display: flex; flex-direction: column; align-items: flex-end; margin-right: 15px;">
                      <div style="font-size: 10px; color: #a78bfa; text-transform: uppercase; letter-spacing: 1px; font-weight: 600;">LLM Token Limit</div>
                      <div style="display: flex; align-items: center; gap: 6px;">
                          <div style="width: 50px; height: 4px; background: rgba(255,255,255,0.1); border-radius: 2px; overflow: hidden;">
                              <div id="tokenProgressBar" style="width: 100%; height: 100%; background: #10b981; transition: width 0.3s, background 0.3s;"></div>
                          </div>
                          <span id="tokenCounter" style="font-family: 'JetBrains Mono', monospace; font-size: 13px; font-weight: 700; color: #fff;">1,000,000</span>
                      </div>
                  </div>
'''

target_anchor = '<div class="action-buttons">'
if target_anchor in html:
    html = html.replace(target_anchor, target_anchor + '\n' + new_token_widget)

with open('templates/dashboard.html', 'w', encoding='utf-8') as f:
    f.write(html)
print('Dashboard UI token widget fixed and moved.')
