import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

with open("matrix_vps.json", "r", encoding="utf-8") as f:
    data = json.load(f)

matrix = data.get("matrix", [])
print(f"Total assets in live matrix: {len(matrix)}")

# Filter USDT pairs
usdt_pairs = [x for x in matrix if "USDT" in x.get("symbol", "")]
usdt_pairs.sort(key=lambda x: x.get("ranking_score", 0), reverse=True)

print("\n" + "="*80)
print("=== LIVE VPS MATRIX - TOP 15 RANKED ASSETS ===")
print("="*80)

for i, x in enumerate(usdt_pairs[:20]):
    sym = x.get("symbol")
    score = x.get("ranking_score", 0)
    price = x.get("price", 0)
    chg = x.get("change_pct", 0)
    vol = x.get("volume_ratio", 1.0) or 1.0
    xr = x.get("xray_ratio") or 0.0
    rsi = x.get("rsi", 50)
    sig = x.get("decision", "HOLD")
    badge = x.get("badge", "")
    reason = x.get("reason", "")
    
    # 2 Kontrol check:
    # 1. Hacim Onayi: vol >= 1.2
    # 2. X-Ray Onayi: xr >= 1.15
    # 3. Dusus korumasi: chg >= -1.5%
    c1 = vol >= 1.2
    c2 = xr >= 1.15
    k2_status = "ONAYLANDI (BUY PASS)" if (c1 and c2) else ("TUZAK/RISK (BLOCK)" if xr < 1.0 else "BEKLEMEDE")
    
    print(f"#{i+1:02d} {sym:<10} | Skor: {score:<5.1f} | Fiyat: {price:<9.4f} | 24h: {chg:>+6.2f}% | Hacim: {vol:4.2f}x | XR: {xr:4.2f} | RSI: {rsi:4.1f} | Sinyal: {sig:<6} | +2 KONTROL: {k2_status}")
    if badge or reason:
        print(f"     Etiket: {badge} | Sebep: {reason}")

print("\n" + "="*80)
print("=== KONTROL TESTI GECENLER (XR >= 1.15 & Hacim >= 1.2x) ===")
print("="*80)

passed = [x for x in usdt_pairs if (x.get("xray_ratio") or 0) >= 1.15 and (x.get("volume_ratio") or 0) >= 1.2]
if passed:
    for x in passed:
        print(f"★ {x.get('symbol')}: Skor={x.get('ranking_score')} | Fiyat={x.get('price')} | 24h={x.get('change_pct')}% | Hacim={x.get('volume_ratio')}x | XR={x.get('xray_ratio')} | Sinyal={x.get('decision')}")

else:
    print("Su an her iki sarti (Hacim >= 1.2x VE XR >= 1.15) ayni anda saglayan varlik yok!")

print("\n" + "="*80)
print("=== XR EN YUKSEK OLANLAR (BASKIN ALICI AKISI) ===")
print("="*80)
top_xr = sorted(usdt_pairs, key=lambda x: (x.get("xray_ratio") or 0.0), reverse=True)[:5]
for x in top_xr:
    print(f"▲ {x.get('symbol')}: XR={x.get('xray_ratio')} | Hacim={x.get('volume_ratio')}x | Fiyat={x.get('price')} | 24h={x.get('change_pct')}% | Sinyal={x.get('decision')}")

print("\n" + "="*80)
print("=== HACIM PATLAMASI EN YUKSEK OLANLAR ===")
print("="*80)
top_vol = sorted(usdt_pairs, key=lambda x: (x.get("volume_ratio") or 0.0), reverse=True)[:5]
for x in top_vol:
    print(f"⚡ {x.get('symbol')}: Hacim={x.get('volume_ratio')}x | XR={x.get('xray_ratio')} | Fiyat={x.get('price')} | 24h={x.get('change_pct')}% | Sinyal={x.get('decision')}")

