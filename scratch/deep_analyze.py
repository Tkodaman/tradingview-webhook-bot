import json

def analyze():
    try:
        with open('scratch/live_matrix.json', 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        grouped = data.get('grouped', {})
        
        print("=== DERİN ANALİZ RAPORU ===")
        
        for market in ['CRYPTO', 'BIST', 'NASDAQ']:
            for item in grouped.get(market, []):
                if item.get('symbol') in ['TRXUSDT', 'BIMAS', 'NEARUSDT', 'INTU', 'UNIUSDT']:
                    print(f"--- {item.get('symbol')} ---")
                    for k, v in item.items():
                        print(f"{k}: {v}")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == '__main__':
    analyze()
