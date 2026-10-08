import json

def analyze_matrix():
    try:
        with open('scratch/live_matrix.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        grouped = data.get('grouped', {})
        results = []
        
        for market in ['CRYPTO', 'NASDAQ', 'BIST']:
            assets = grouped.get(market, [])
            if not assets:
                continue
            
            # Sadece geçerli objeleri alalım
            assets = [a for a in assets if isinstance(a, dict) and a.get('symbol')]
            
            # Normal fırsatları güvene göre sırala (Mor olmayanlar)
            normals = [a for a in assets if not (a.get('is_reversal') and str(a.get('is_reversal')).lower() != 'false')]
            normals.sort(key=lambda x: float(x.get('confidence_score', 0)), reverse=True)
            
            # Mor olanları güvene göre sırala
            purples = [a for a in assets if a.get('is_reversal') and str(a.get('is_reversal')).lower() != 'false']
            purples.sort(key=lambda x: float(x.get('confidence_score', 0)), reverse=True)
            
            results.append(f"=== {market} PİYASASI ===")
            
            if normals:
                results.append("🟢 EN İYİ 3 TREND/MOMENTUM FIRSATI (NORMAL):")
                for n in normals[:3]:
                    sym = n.get('symbol')
                    score = n.get('confidence_score', 0)
                    vol = n.get('volume_ratio', 1)
                    rsi = n.get('rsi', 0)
                    chg = n.get('change_pct', 0)
                    results.append(f" - {sym} | Skor: {score} | Hacim: {vol}x | RSI: {rsi} | Değişim: %{chg}")
            
            if purples:
                results.append("🟣 EN İYİ GERİ DÖNÜŞ / KANAMA FIRSATI (MOR KUTU):")
                for p in purples[:2]:
                    sym = p.get('symbol')
                    score = p.get('confidence_score', 0)
                    vol = p.get('volume_ratio', 1)
                    rsi = p.get('rsi', 0)
                    chg = p.get('change_pct', 0)
                    results.append(f" - {sym} | Skor: {score} | Hacim: {vol}x | RSI: {rsi} | Değişim: %{chg}")
            
            results.append("")
            
        print("\n".join(results))
            
    except Exception as e:
        print(f"Hata: {e}")

if __name__ == '__main__':
    analyze_matrix()
