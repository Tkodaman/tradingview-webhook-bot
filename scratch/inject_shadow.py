import os

file_path = 'templates/dashboard.html'
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

injection = """
        <!-- TIER-1 SHADOW ARENA PANEL INTEGRATION -->
        <div class="mt-12 mb-12">
            <div class="flex items-center space-x-3 mb-4">
                <div class="w-2 h-8 bg-blue-500 rounded-full shadow-[0_0_10px_rgba(59,130,246,0.8)]"></div>
                <h2 class="text-2xl font-bold text-white tracking-wide uppercase">GÖLGE ARENA <span class="text-slate-500 text-lg">(Paper Trading & ML Eğitim Modülü)</span></h2>
            </div>
            <div class="w-full bg-slate-900 rounded-2xl border border-slate-700 overflow-hidden shadow-2xl" style="height: 800px;">
                <iframe src="/shadow" width="100%" height="100%" frameborder="0"></iframe>
            </div>
        </div>
"""

if '<!-- TIER-1 SHADOW ARENA PANEL INTEGRATION -->' not in content:
    # Inject it before the closing </body> tag
    if '</body>' in content:
        content = content.replace('</body>', injection + '\n</body>')
        
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print('Enjeksiyon basarili.')
else:
    print('Zaten eklenmis.')
