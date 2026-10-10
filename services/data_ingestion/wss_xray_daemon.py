import asyncio
import json
import time
import os
import websockets
from collections import defaultdict
from core.logger import logger
from services.data_ingestion.asset_universe_manager import asset_universe_manager

CACHE_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wss_xray_cache.json")

# Bellek içi toplayıcı: Taker Buy ve Total Volume
# sym -> {"taker_buy": float, "total": float, "last_update": timestamp, "kline_history": list, "current_kline_t": int}
xray_data = defaultdict(lambda: {"taker_buy": 0.0, "total": 0.0, "last_update": 0, "kline_history": [], "current_kline_t": 0})

async def binance_xray_stream():
    """
    Tüm kripto assetleri için Binance aggTrade (veya kline) stream'ine bağlanır.
    İfşa olmadan (REST limitlerine takılmadan) X-Ray verisini dinler.
    Biz kline (15m) dinleyeceğiz, çünkü taker buy / total volume kline'da var.
    """
    logger.info("[WSS DAEMON] Binance X-Ray WebSocket kalkanı başlatılıyor...")
    
    universe = asset_universe_manager.get_universe()
    crypto_symbols = [asset["symbol"].replace("BINANCE:", "").lower() for asset in universe if asset["market"] == "CRYPTO"]
    
    if not crypto_symbols:
        logger.warning("[WSS DAEMON] İzlenecek kripto asset bulunamadı.")
        return

    # Sockets 1024 symbol'den fazlasını desteklemez ama bizde az var.
    # Kline 15m dinleyelim: <symbol>@kline_15m
    streams = [f"{sym}@kline_15m" for sym in crypto_symbols]
    stream_url = f"wss://stream.binance.com:9443/stream?streams={'/'.join(streams)}"

    while True:
        try:
            async with websockets.connect(stream_url) as websocket:
                logger.info(f"[WSS DAEMON] {len(crypto_symbols)} varlık için WSS tüneli kuruldu (Görünmez Mod Aktif).")
                while True:
                    response = await websocket.recv()
                    data = json.loads(response)
                    
                    if "data" in data and "k" in data["data"]:
                        k = data["data"]["k"]
                        sym = data["data"]["s"].upper()
                        
                        total_vol = float(k["q"])  # Quote Asset Volume (Total USDT)
                        taker_buy_vol = float(k["Q"])  # Taker Buy Quote Asset Volume (Taker USDT)
                        kline_start_time = int(k["t"]) # Candle start time in ms
                        
                        # 45D Kümülatif (Rolling Window) Geçmiş Mum Kontrolü
                        if xray_data[sym]["current_kline_t"] == 0:
                            xray_data[sym]["current_kline_t"] = kline_start_time
                            
                        # Eğer mum değiştiyse (Yeni 15 Dk başladıysa), kapanan mumu geçmiş havuzuna at
                        if kline_start_time != xray_data[sym]["current_kline_t"]:
                            old_taker_buy = xray_data[sym].get("taker_buy", 0.0)
                            old_total = xray_data[sym].get("total", 0.0)
                            xray_data[sym]["kline_history"].append({"taker_buy": old_taker_buy, "total": old_total})
                            
                            # Sadece son 2 kapanmış mumu (30 Dk) havuzda tut. +1 Mevcut = 45D Kümülatif
                            if len(xray_data[sym]["kline_history"]) > 2:
                                xray_data[sym]["kline_history"].pop(0)
                                
                            xray_data[sym]["current_kline_t"] = kline_start_time
                        
                        xray_data[sym]["taker_buy"] = taker_buy_vol
                        xray_data[sym]["total"] = total_vol
                        xray_data[sym]["last_update"] = time.time()
                        
                        # Her 10 saniyede bir JSON dosyasına dumpla
                        if time.time() % 10 < 1:
                            _dump_to_cache()
                            
        except Exception as e:
            logger.error(f"[WSS DAEMON] Bağlantı koptu veya hata: {e}. 5sn sonra yeniden denenecek...")
            await asyncio.sleep(5)

def _dump_to_cache():
    # Cache dosyasına yaz, böylece tradingview_live_client.py buradan okuyabilsin.
    output = {}
    now = time.time()
    for sym, stats in xray_data.items():
        if now - stats["last_update"] < 900: # Son 15 dk
            # 45 Dakikalık Gerçek Kümülatif Toplam (Geçmiş 30D + Canlı 15D)
            hist_taker_buy = sum([h["taker_buy"] for h in stats["kline_history"]])
            hist_total = sum([h["total"] for h in stats["kline_history"]])
            
            final_taker_buy = hist_taker_buy + stats["taker_buy"]
            final_total = hist_total + stats["total"]
            final_taker_sell = final_total - final_taker_buy
            
            if final_taker_sell > 0:
                raw_ratio = round(final_taker_buy / final_taker_sell, 2)
            else:
                raw_ratio = 9.99
                
            # Kaos Önleyici EMA (Hala koruma olarak kalabilir, ama asıl işi Rolling Window yapıyor)
            old_ratio = stats.get("smoothed_ratio", raw_ratio)
            smoothed_ratio = round((old_ratio * 0.90) + (raw_ratio * 0.10), 2)
            stats["smoothed_ratio"] = smoothed_ratio
            
            output[sym] = {
                "xray_ratio": smoothed_ratio,
                "taker_buy": final_taker_buy,
                "taker_sell": final_taker_sell,
                "ts": stats["last_update"]
            }
            
    with open(CACHE_FILE, "w") as f:
        json.dump(output, f)

if __name__ == "__main__":
    try:
        asyncio.run(binance_xray_stream())
    except KeyboardInterrupt:
        logger.info("[WSS DAEMON] Kapatılıyor...")
