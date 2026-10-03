import logging
import asyncio
import json
from typing import Dict, Any
from services.broker.factory import get_broker
from services.ai.llm_master_agent import llm_master_agent

logger = logging.getLogger(__name__)

class AIRiskManager:
    """
    OKX Agent Trade Kit Konsepti:
    YZ'nin (LLM) salt bir danışman olmaktan çıkıp, doğrudan "İşlem İptali (Cancel Order)"
    ve "TP/SL Güncelleme" yetkilerine (Function Calling) sahip olduğu aktif risk motoru.
    """
    def __init__(self):
        self.broker = get_broker()
        self.is_running = False

    async def start_risk_loop(self, interval_seconds: int = 120):
        """Her X saniyede bir açık pozisyonları tarayıp YZ'ye sunar."""
        self.is_running = True
        logger.info("[AI RISK MANAGER] OKX Agent Tool-Calling konsepti devrede. YZ risk denetleyicisi aktif.")
        while self.is_running:
            try:
                await self.scan_open_positions_and_manage()
            except Exception as e:
                logger.error(f"[AI RISK MANAGER] Loop hatası: {e}")
            await asyncio.sleep(interval_seconds)

    async def scan_open_positions_and_manage(self):
        """Açık pozisyonları tarar ve kritik durumlarda YZ'ye müdahale yetkisi verir."""
        try:
            positions = await asyncio.to_thread(self.broker.get_open_positions)
            if not positions:
                return

            logger.info(f"🛡️ [AI RISK MANAGER] {len(positions)} açık pozisyon YZ denetiminden geçiyor...")
            
            for pos in positions:
                symbol = pos.get('symbol')
                unrealized_pl_pcnt = float(pos.get('unrealized_plpc', 0)) * 100
                current_price = float(pos.get('current_price', 0))
                
                # Sadece aşırı hareketlerde YZ'yi rahatsız et (örn: %2'den fazla zarar veya %5'ten fazla kâr)
                if unrealized_pl_pcnt < -2.0 or unrealized_pl_pcnt > 5.0:
                    await self._ask_ai_for_intervention(symbol, unrealized_pl_pcnt, current_price)
                    
        except Exception as e:
            logger.error(f"[AI RISK MANAGER] Pozisyon tarama hatası: {e}")

    async def _ask_ai_for_intervention(self, symbol: str, pnl_pct: float, price: float):
        """YZ'ye pozisyonun durumunu sunar ve JSON formatında aksiyon (Tool Calling) bekler."""
        if not llm_master_agent.is_ready():
            return
            
        prompt = f"""
        Şu an {symbol} pozisyonumuz var. Anlık kâr/zarar: %{pnl_pct:.2f}. Anlık Fiyat: {price}.
        Piyasa koşullarına göre bu pozisyona müdahale etmek ister misin?
        Eğer müdahale edeceksen aşağıdaki JSON formatlarından BİRİNİ dön, başka hiçbir metin yazma:
        1. {{"action": "CLOSE_POSITION", "reason": "Buraya sebep yaz"}}
        2. {{"action": "UPDATE_SL", "new_sl": <yeni_fiyat>, "reason": "Buraya sebep yaz"}}
        3. {{"action": "HOLD", "reason": "Beklemeye devam"}}
        """
        
        try:
            response = await asyncio.to_thread(
                llm_master_agent.chat,
                user_message=prompt, 
                system_prompt="Sen doğrudan broker'a emir gönderen bir risk yöneticisisin. Sadece geçerli JSON dön.", 
                max_tokens=150
            )
            
            # Basit JSON ayıklayıcı
            start_idx = response.find("{")
            end_idx = response.rfind("}")
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx+1]
                decision = json.loads(json_str)
                await self._execute_ai_tool(symbol, decision)
                
        except Exception as e:
            logger.debug(f"[AI RISK MANAGER] YZ yanıtı ayrıştırılamadı (Geçerli bir JSON olmayabilir): {e}")

    async def _execute_ai_tool(self, symbol: str, decision: Dict[str, Any]):
        action = decision.get("action")
        reason = decision.get("reason", "Belirtilmedi")
        
        if action == "CLOSE_POSITION":
            logger.warning(f"🚨 [AI DIRECT ACTION] YZ {symbol} pozisyonunu acil kapatma kararı aldı! Sebep: {reason}")
            try:
                await asyncio.to_thread(self.broker.close_position, symbol)
                logger.info(f"✅ [AI DIRECT ACTION] {symbol} pozisyonu YZ tarafından başarıyla kapatıldı.")
            except Exception as e:
                logger.error(f"❌ [AI DIRECT ACTION] Kapatma başarısız: {e}")
                
        elif action == "UPDATE_SL":
            new_sl = decision.get("new_sl")
            logger.info(f"🛡️ [AI DIRECT ACTION] YZ {symbol} için SL'yi {new_sl} seviyesine çekiyor. Sebep: {reason}")
            # Alpaca SL güncelleme mantığı buraya eklenebilir. 
            # (Şimdilik sadece logluyoruz, tam entegrasyon broker destekliyorsa yapılır)
            
        elif action == "HOLD":
            logger.info(f"✅ [AI DIRECT ACTION] YZ pozisyonu tutmaya (HOLD) karar verdi. Sebep: {reason}")

ai_risk_manager = AIRiskManager()
