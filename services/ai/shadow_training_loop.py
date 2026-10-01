import asyncio
import logging
import random
from datetime import datetime
from services.ai.llm_master_agent import experience_memory_engine, llm_master_agent

logger = logging.getLogger(__name__)

class ShadowTrainingLoop:
    """
    Superalgos Konsepti: Walk-Forward Validation (Kendi Kendini Eğitme Döngüsü)
    Bot boşta kaldığı anlarda, geçmiş işlemleri (Memory/Database) tekrar
    YZ'nin (LLM) önüne koyarak "Şimdi olsa ne yapardın?" diye sorar.
    Bu sayede bot, piyasa değişmedikçe bile kendi hatalarından öğrenerek kusursuzlaşır.
    """
    
    def __init__(self):
        self.is_running = False

    async def start_training_loop(self, interval_seconds: int = 3600):
        """Arka planda (Daemon) sürekli çalışan simülasyon eğitimi."""
        self.is_running = True
        logger.info("[SHADOW TRAINING] Walk-Forward Validation (Superalgos Modu) başlatıldı. Bot boş vaktinde kendi geçmişiyle satranç oynayacak.")
        
        while self.is_running:
            try:
                await self._run_simulation_step()
            except Exception as e:
                logger.error(f"[SHADOW TRAINING] Simülasyon hatası: {e}")
            
            # Belirlenen süre kadar dinlen (Default 1 saat)
            await asyncio.sleep(interval_seconds)

    async def _run_simulation_step(self):
        """Geçmiş bir işlemi çeker ve YZ'yi onun üzerinde terletir."""
        if not llm_master_agent.is_ready():
            return
            
        history = experience_memory_engine.get_relevant_experiences("market", k=3)
        if not history:
            logger.debug("[SHADOW TRAINING] Eğitilecek yeterli geçmiş işlem bulunamadı.")
            return
            
        # Rastgele bir geçmiş işlem seç
        past_trade = random.choice(history)
        
        # O anki şartları yeniden yarat (simülasyon)
        prompt = f"""
        [SHADOW TRAINING - WALK FORWARD VALIDATION]
        Bu bir geçmiş işlem simülasyonudur. Amacımız geçmiş kararı eleştirmek ve kusursuzlaşmaktır.
        
        Geçmiş Olay:
        {past_trade}
        
        Soru: Bugünkü aklınla, bu işlemdeki göstergeleri görseydin kararın farklı olur muydu? 
        Yanıtını kısaca analiz et ve 'DERS ALINDI' diyerek neyi daha iyi yapabileceğini belirt.
        """
        
        response = await asyncio.to_thread(
            llm_master_agent.chat,
            user_message=prompt, 
            system_prompt="Sen acımasız bir eleştirmensin. Kendi geçmiş kararlarını didik didik edip kusursuzlaşmaya çalışıyorsun.", 
            max_tokens=200
        )
        
        logger.info(f"🧠 [SHADOW TRAINING ÇIKTISI]:\n{response}")
        
        # Öğrenilen dersi tekrar hafızaya yaz (Kendini pekiştirme)
        experience_memory_engine.add_experience(
            text=f"SHADOW_TRAINING_LESSON: {response}",
            metadata={"type": "training_lesson", "timestamp": datetime.now().isoformat()}
        )
        logger.info("[SHADOW TRAINING] Yeni öğrenilen ders RAG (Hafıza) vektör veritabanına kalıcı olarak işlendi.")

shadow_trainer = ShadowTrainingLoop()
