import requests, json
res = requests.get('http://127.0.0.1:8000/api/market/live-matrix')
if res.status_code == 200:
    data = res.json()
    keys_of_interest = ['AAVEUSDT', 'SOLUSDT']
    for k in keys_of_interest:
        v = data.get(k)
        if v:
            print(f"{k}: Price={v.get('price')} VolRatio={v.get('volume_ratio')} RSI={v.get('rsi')} Score={v.get('ai_confidence_score')}")
        else:
            print(f"{k} not found in matrix")
    
    print('\n--- TOP TARGETS (Vol > 0.9, RSI < 65) ---')
    sorted_data = sorted([v for v in data.values() if v.get('volume_ratio',0)>0.9 and v.get('rsi',50)<65], key=lambda x: x.get('ai_confidence_score', 0), reverse=True)
    for v in sorted_data[:5]:
        print(f"{v.get('symbol')}: Score={v.get('ai_confidence_score')} Vol={v.get('volume_ratio')} RSI={v.get('rsi')}")
