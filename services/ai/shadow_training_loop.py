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
        [SHADOW TRAINING - YARGI SONRASI ML DÜZELTME VE YAPILANDIRMA]
        Bu bir geçmiş işlem simülasyonudur. Amacımız geçmiş kararı eleştirmek ve botun karar mekanizmasını (ağırlıklarını) güncellemektir.
        
        Geçmiş Olay:
        {past_trade}
        
        Görev:
        1. Bugünkü aklınla bu kararı eleştir ve neyi yanlış/doğru yaptığını açıkla.
        2. Yüce Divan'ın ajan ağırlıklarını (toplam 1.0 olacak şekilde) bu derse göre yeniden yapılandır.
        Örneğin hacim eksikse MACRO'yu artır, haber yanılttıysa NEWS'i düşür.
        
        Lütfen yanıtını SADECE aşağıdaki JSON formatında dön:
        {{
            "lesson": "DERS ALINDI: ...",
            "weights": {{"OBI": 0.10, "MACRO": 0.20, "WHALE": 0.20, "NEWS": 0.10, "REGIME": 0.15, "CHIEF_JUSTICE": 0.25}}
        }}
        """
        
        response = await asyncio.to_thread(
            llm_master_agent.chat,
            user_message=prompt, 
            system_prompt="Sen acımasız bir eleştirmensin ve Yüce Divan'ın ML yapılandırma mühendisisin. Yalnızca geçerli JSON dön.", 
            max_tokens=400
        )
        
        logger.info(f"🧠 [SHADOW TRAINING ÇIKTISI]:\n{response}")
        
        try:
            import json, os
            start_idx = response.find("{")
            end_idx = response.rfind("}")
            if start_idx != -1 and end_idx != -1:
                data = json.loads(response[start_idx:end_idx+1])
                lesson = data.get("lesson", str(response))
                new_weights = data.get("weights")
                
                # Ağırlıkları Kaydet (Yargı Sonrası ML Düzeltme / Yapılandırma)
                if new_weights and isinstance(new_weights, dict):
                    weights_path = os.path.join(os.path.dirname(__file__), 'dynamic_weights.json')
                    with open(weights_path, 'w') as f:
                        json.dump(new_weights, f, indent=4)
                    logger.info("⚙️ [ML YAPILANDIRMA] Yargı sonrası botun konsey ağırlıkları otonom olarak güncellendi!")
                
                # Öğrenilen dersi tekrar hafızaya yaz (Kendini pekiştirme)
                experience_memory_engine.add_experience(
                    text=f"SHADOW_TRAINING_LESSON: {lesson}",
                    metadata={"type": "training_lesson", "timestamp": datetime.now().isoformat()}
                )
                logger.info("[SHADOW TRAINING] Yeni öğrenilen ders RAG vektör veritabanına işlendi.")
        except Exception as e:
            logger.error(f"[SHADOW TRAINING] JSON Ayrıştırma veya ML Yapılandırma Hatası: {e}")

shadow_trainer = ShadowTrainingLoop()
