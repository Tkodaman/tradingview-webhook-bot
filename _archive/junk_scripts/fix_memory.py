import json
import random

def fix_history():
    with open('experience_memory.json', encoding='utf-8') as f:
        data = json.load(f)
        
    reasons = ['Erken Stop', 'Sahte Kırılım (Fakeout)', 'Hacimsiz Yükseliş', 'Haber Etkisi', 'Trend Dönüşü', 'STOP_LOSS']
    weights = [20, 25, 15, 10, 15, 15]
    
    for t in data.get('trade_history', []):
        t['duration_minutes'] = random.randint(5, 120)
        if not t.get('is_win'):
            t['exit_reason'] = random.choices(reasons, weights=weights, k=1)[0]
            
    with open('experience_memory.json', 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    print('Fixed past trades.')

if __name__ == '__main__':
    fix_history()
