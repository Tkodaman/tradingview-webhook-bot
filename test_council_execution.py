import logging
import json

logging.basicConfig(level=logging.INFO, format="%(message)s")

# Sentetik auto_runner simülasyon fonksiyonu
def evaluate_synthetic_asset(sym, data):
    score = data.get("initial_score", 15.0)
    vol_ratio = data.get("vol_ratio", 1.0)
    xray_val = data.get("xray_ratio", 1.0)
    chg_pct = data.get("change_pct", 0.0)
    
    reports = []
    
    # =========================================================
    # DİNAMİK KUANT SENTEZLEYİCİ (VEKTÖREL HACİM & X-RAY MOMENTUMU)
    # =========================================================
    xr_direction = xray_val - 1.0
    magnitude = vol_ratio
    vector_impact = xr_direction * magnitude * 15.0

    score += vector_impact

    if vector_impact <= -15.0:
        reports.append(f"[VECTOR RISK] Ölümcül Hacimli Satış. Penalty: {vector_impact:.1f}. Score is now {score:.1f}")
    elif vector_impact >= 15.0:
        reports.append(f"[VECTOR QUANT] Muazzam Alım (Compound). Bonus: +{vector_impact:.1f}. Score is now {score:.1f}")
    elif 8.0 <= vector_impact < 15.0 and chg_pct <= 0.5:
        reports.append(f"[VECTOR MARKET] Gizli Akümülasyon (Decoupling). Bonus: +{vector_impact:.1f}. Score is now {score:.1f}")
        
    return score, reports

# Konsey Test Vakaları
test_cases = [
    {"name": "Normal Pump", "data": {"initial_score": 15, "vol_ratio": 1.5, "xray_ratio": 1.1, "change_pct": 2.0}},
    {"name": "Fakeout (Death Trap)", "data": {"initial_score": 25, "vol_ratio": 3.0, "xray_ratio": 0.6, "change_pct": 5.0}},
    {"name": "Kusursuz Fırtına (Compound)", "data": {"initial_score": 20, "vol_ratio": 3.5, "xray_ratio": 1.6, "change_pct": 4.0}},
    {"name": "Düşen Bıçak (Falling Knife)", "data": {"initial_score": 10, "vol_ratio": 4.0, "xray_ratio": 1.8, "change_pct": -15.0}},
    {"name": "Hafif Baskı (True Decoupling)", "data": {"initial_score": 12, "vol_ratio": 2.2, "xray_ratio": 1.4, "change_pct": -0.5}},
    {"name": "Eksi Başlangıç Puanı (Negative Base)", "data": {"initial_score": -5, "vol_ratio": 4.0, "xray_ratio": 2.0, "change_pct": 6.0}}
]

print("=== KONSEY BACKTEST RAPORU ===")
for case in test_cases:
    print(f"\n--- Senaryo: {case['name']} ---")
    final_score, reps = evaluate_synthetic_asset(case["name"], case["data"])
    for r in reps:
        print(r)
    print(f"Final Skor: {final_score:.1f}")

