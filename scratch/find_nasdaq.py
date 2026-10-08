import json

def find_best_nasdaq():
    try:
        with open('scratch/live_matrix.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        nasdaq = data.get('grouped', {}).get('NASDAQ', [])
        
        print("=== KUSURSUZ NASDAQ ADAYLARI ===")
        found = False
        
        # Önce skora göre sıralayalım
        nasdaq.sort(key=lambda x: float(x.get('confidence_score', 0) or 0), reverse=True)
        
        for item in nasdaq:
            vol = float(item.get('volume_ratio', 0) or 0)
            score = float(item.get('confidence_score', 0) or 0)
            sym = item.get('symbol')
            reason = str(item.get('reason', ''))
            badge = str(item.get('badge', ''))
            phase = str(item.get('momentum_phase', ''))
            cmf = float(item.get('cmf', 0) or 0)
            rsi = float(item.get('rsi', 0) or 0)
            chg = float(item.get('change_pct', 0) or 0)
            
            # Risk/Fakeout veya yoğun bakım engeli yemiş olanları atla
            if "RISK_BLOCK" in badge or "FAKEOUT" in phase or "Yoğun Bakım" in reason or score < 40:
                continue
                
            found = True
            print(f"\n--- {sym} ---")
            print(f"Skor: {score} | Hacim: {vol} | RSI: {rsi} | CMF: {cmf} | Değişim: %{chg}")
            print(f"Faz: {phase}")
            print(f"Durum: {badge} - {reason}")
            print(f"Score Breakdown: {item.get('score_breakdown', {})}")
            
        if not found:
            print("Maalesef şu an 'kusursuz' diyebileceğimiz, fakeout yemeyen bir Nasdaq hissesi matriste yok.")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    find_best_nasdaq()
