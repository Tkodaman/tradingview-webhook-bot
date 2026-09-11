with open('routers/market_router.py', 'r', encoding='utf-8') as f:
    text = f.read()

# We need to inject confidence_score logic and slice the arrays
# We will find grouped_matrix = {

search_str = '''    grouped_matrix = {
        "CRYPTO": [m for m in matrix_results if m["market"] == "CRYPTO"],
        "BIST": [m for m in matrix_results if m["market"] == "BIST"],
        "NASDAQ": [m for m in matrix_results if m["market"] == "NASDAQ"]
    }'''

replacement_str = '''    # AI Güven Skoru Entegrasyonu
    from services.engine.experience_memory_engine import experience_memory_engine
    confidence_data = experience_memory_engine.get_asset_confidence_index()
    confidence_map = {item["symbol"].upper(): item for item in confidence_data}
    
    for m in matrix_results:
        sym = m["symbol"].upper()
        ai_data = confidence_map.get(sym, {})
        # Eğer geçmiş işlem yoksa formüle dayalı bir başlangıç skoru ver (RSI + MACD + Hacim bazlı)
        default_score = min(99.0, max(45.0, 50.0 + (m["score"] * 5.0) + (m["change_pct"] * 2.0)))
        
        m["confidence_score"] = float(ai_data.get("confidence_score", round(default_score, 1)))
        m["expertise_level"] = ai_data.get("expertise_level", "🟡 NÖTR / DENGELİ")
        m["ai_action"] = ai_data.get("action_recommendation", "🟡 Standart İnceleme")

    grouped_matrix = {
        "CRYPTO": sorted([m for m in matrix_results if m["market"] == "CRYPTO"], key=lambda x: x["confidence_score"], reverse=True)[:12],
        "BIST": sorted([m for m in matrix_results if m["market"] == "BIST"], key=lambda x: x["confidence_score"], reverse=True)[:10],
        "NASDAQ": sorted([m for m in matrix_results if m["market"] == "NASDAQ"], key=lambda x: x["confidence_score"], reverse=True)[:16]
    }'''

if search_str in text:
    text = text.replace(search_str, replacement_str)
    with open('routers/market_router.py', 'w', encoding='utf-8') as f:
        f.write(text)
    print("Patched market_router.py")
else:
    print("Could not find search string in market_router.py")
