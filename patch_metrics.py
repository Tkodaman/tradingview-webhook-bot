import re

with open('services/engine/experience_memory_engine.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Disable dynamic sim completely (set it to False)
content = re.sub(
    r'use_dynamic_sim = len\(self\.trade_history\) < 20',
    'use_dynamic_sim = False  # Her zaman gercek veri',
    content
)

# Update Bar Chart to include percentages (pay payda bölüşümü)
new_bar_chart = '''        # 4. Bar Chart: Hata Türleri / Zarar Nedenleri
        if use_dynamic_sim:
            bar_labels = ["Hacim Çekilmesi", "Direnç Reddi", "Ani Volatilite", "Zaman Aşımı", "Stop-Loss"]
            bar_values = [random.randint(12, 18), random.randint(8, 14), random.randint(5, 9), random.randint(3, 7), random.randint(1, 4)]
            bar_tooltips = [f"{l} Kaynaklı Hata | {v} Kez" for l, v in zip(bar_labels, bar_values)]
        else:
            error_counts = defaultdict(int)
            total_errors = 0
            for t in self.trade_history:
                pnl = getattr(t, 'pnl_pct', 0)
                if not getattr(t, 'is_win', pnl > 0) or pnl < 0:
                    reason = getattr(t, 'exit_reason', "Bilinmeyen") or "Bilinmeyen"
                    if len(reason) > 20: reason = reason[:17] + "..."
                    error_counts[reason] += 1
                    total_errors += 1
            bar_labels, bar_values, bar_tooltips = [], [], []
            for r, c in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
                pct = (c / total_errors * 100) if total_errors > 0 else 0
                bar_labels.append(r); bar_values.append(c); bar_tooltips.append(f"Neden: {r} | {c} Kez (Ağırlık: %{pct:.1f})")
            if not bar_labels:
                bar_labels, bar_values, bar_tooltips = ["Kusursuz İlerleyiş"], [0], ["Hata Bulunmuyor"]'''

# We need to replace the old bar chart section
old_bar_pattern = r'# 4\. Bar Chart: Hata TǬrleri / Zarar Nedenleri.*?(?=# 5\. Area Chart)'
# Because of utf-8 encoding and possible weird characters, let's just do a string replacement on the block
# Let's use a simpler approach: regex search and replace
content = re.sub(
    r'# 4\. Bar Chart:.*?(?=# 5\. Area Chart)',
    new_bar_chart + '\n\n        ',
    content,
    flags=re.DOTALL
)

with open('services/engine/experience_memory_engine.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Patched experience_memory_engine.py")
