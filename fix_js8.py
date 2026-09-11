with open(r'templates\dashboard.html', 'r', encoding='utf-8') as f:
    text = f.read()

text = text.replace("updateChartData(summary.account_balance);", "// updateChartData(summary.account_balance);")

with open(r'templates\dashboard.html', 'w', encoding='utf-8') as f:
    f.write(text)

print("Commented out updateChartData()")
