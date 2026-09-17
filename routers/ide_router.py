import os
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import google.generativeai as genai
from core.logger import logger
from services.market_feed.live_stream import live_trade_manager

router = APIRouter(prefix="/api/ide", tags=["ide"])

import asyncio
from google.api_core.exceptions import ResourceExhausted, TooManyRequests
from openai import AsyncOpenAI

async def _call_gemini_with_retry(model, prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await model.generate_content_async(prompt)
        except Exception as e:
            if "429" in str(e) or isinstance(e, (ResourceExhausted, TooManyRequests)):
                if attempt == max_retries - 1:
                    raise e
                wait_time = 4 + (attempt * 2)
                logger.warning(f"Gemini API Quota Exceeded (429). Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                await asyncio.sleep(wait_time)
            else:
                raise e

async def _call_openai_with_retry(client, model_name, prompt, max_retries=3):
    for attempt in range(max_retries):
        try:
            response = await client.chat.completions.create(
                model=model_name,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.7
            )
            print(f"AI Model Executed: {response.model}")
            print(f"Token Usage: {response.usage}")
            return response.choices[0].message.content
        except Exception as e:
            if "429" in str(e):
                if attempt == max_retries - 1:
                    raise e
                wait_time = 4 + (attempt * 2)
                logger.warning(f"OpenAI API Quota Exceeded (429). Retrying in {wait_time}s... (Attempt {attempt+1}/{max_retries})")
                await asyncio.sleep(wait_time)
            else:
                raise e



class IDETriggerRequest(BaseModel):
    query: str
    model_id: str
    
MODEL_COSTS = {
    "gemini-1.5-flash": 1.5,
    "gemini-1.5-pro": 5.0,
    "gemini-3.1-pro-low": 8.0,
    "gemini-3.1-pro": 12.0,
    "gemini-3.6-ultra": 25.0,
    "gemini-3.8-omni": 40.0
}

@router.post("/trigger")
async def trigger_ide_model(req: IDETriggerRequest):
    cost = MODEL_COSTS.get(req.model_id, 5.0)
    
    if live_trade_manager.user_credits < cost:
        raise HTTPException(status_code=400, detail="YETERSİZ KREDİ! Lütfen bakiye yükleyin.")
        
    # Krediyi düş
    live_trade_manager.user_credits -= cost
    
    try:
        llm_provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        
        gemini_model = None
        openai_client = None
        openai_model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-6-astra")
        
        if llm_provider == "openai":
            if openai_model_name == "gpt-6-astra":
                api_key = os.getenv("OPENAI_API_KEY_SECONDARY") or os.getenv("OPENAI_API_KEY")
            else:
                api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise Exception("OPENAI_API_KEY eksik.")
            base_url = os.getenv("OPENAI_BASE_URL")
            openai_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
        else:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise Exception("GEMINI_API_KEY eksik.")
            genai.configure(api_key=api_key)
            gemini_model = genai.GenerativeModel("gemini-1.5-flash")
        
        if req.model_id == "gemini-3.1-pro-low":
            prompt = f"""
Sen bu sistemin YÜCE YÖNETİCİSİ (Admin) olan kullanıcıya hizmet eden "Gemini 3.1 Pro Low" (Admin Özel) danışmanısın.
Kullanıcının (Admin) girdiği talebi analiz et ve botun iç mekanizmaları, hisse/kripto değerlendirmeleri veya stratejik hedefler hakkında DOĞRUDAN yanıt ver. 
Gereksiz uzatmalardan kaçın, kesin ve eyleme geçirilebilir hedefler sun.
Kullanıcı Talebi: {req.query}

Sana sağlanan İndikatörleri, ML Tahminlerini, Haber Duyarlılığını, skill ve Makas Aralığını DİKKATE ALMAK ZORUNDASIN. Bu verileri hiçe sayamazsın. 
Ancak bu analiz sürecinin sonunda asla 'piyasa belirsiz', 'riskli olabilir' gibi kaçamak yorumlar yapamazsın. 
Verileri kendi içinde sentezle ve Çıktını SADECE aşağıdaki JSON formatında ver:

{{
  "rejim": "ADMIN (Gemini 3.1 Pro Low)",
  "vade_tercihi": "Senaryoya uygun vade",
  "stratejik_degerlendirme": "Sentezlenmiş kesin 2 cümlelik karar gerekçesi.",
  "hizli_eylem_karari": "Alınacak net aksiyon özeti",
  "islem_tetikleme": {{
    "action": "BUY" veya "SELL" veya "NONE",
    "symbol": "Sembol (örnek: BTCUSDT)",
    "budget_usd": "Bütçe miktarı sayı olarak (örnek: 250)"
  }},
  "anlik_ozet": "Maliyet={cost} Anlık varlık takibi sağ panelde aktif."
}}
"""
        else:
            prompt = f"""
Sen sisteme entegre edilen "{req.model_id}" kodlu ileri seviye bir yapay zeka finansal motorusun. 
Görevin, kullanıcının girdiği şu talebi piyasa şartlarına göre analiz edip KESİN, TUTARLI ve HIZLI bir çıkarımda bulunmaktır:

[KULLANICI TALEBİ]: {req.query}

Botun asıl amacı: Kâr sağlamak, güvenliği elden bırakmadan cesur ataklar yapmak.
Kullanıcı "Trader_Agent_01" (Sistemi yöneten asıl trader).

[SİSTEM HAFIZASI / ÖĞRENİLMİŞ KURALLAR]:
1. NVDA, AAPL: VIX >18 ise pozisyonu %20 kıs, stop-loss kullan.
2. BTC, ETH: Halving döngüsü, spot ETF akışlarını izle. %5 hacim artışı = kurumsal giriş.
3. BIST Banka: GARAN, AKBNK 3-6 aylık ufukta cazip.
4. Havacılık/Enerji: Petrol $90+ ise havacılıkta marjı daralt, enerjiye yönel.
5. Altın: %5-10 koruma. 2,200-2,500$ bandı.
6. AI: NVDA, AMD kar al seviyelerini genişlet.
7. USD/TRY: Kur riskine karşı %15 döviz tut.
8. Çin Emtia: Dikkatli ol, Altın/Platin alternatif.
9. ETH Layer-2: Likidite riskine dikkat ederek sınırla.
10. VIX > 20: Nakit artır, pozisyonları %25 küçült.
11. SOL: $120 altı kapanış stop, $180+ kırılım yükseliş.

Sana sağlanan İndikatörleri, ML Tahminlerini, Haber Duyarlılığını, skill ve Makas Aralığını DİKKATE ALMAK ZORUNDASIN. Bu verileri hiçe sayamazsın. 
Ancak bu analiz sürecinin sonunda asla 'piyasa belirsiz', 'riskli olabilir' gibi kaçamak yorumlar yapamazsın. 
Verileri kendi içinde sentezle ve Çıktını SADECE aşağıdaki JSON formatında ver:

{{
  "rejim": "{req.model_id} Aktif",
  "vade_tercihi": "Senaryoya uygun vade",
  "stratejik_degerlendirme": "Sentezlenmiş kesin 2 cümlelik karar gerekçesi.",
  "hizli_eylem_karari": "Alınacak net aksiyon özeti",
  "islem_tetikleme": {{
    "action": "BUY" veya "SELL" veya "NONE",
    "symbol": "Sembol (örnek: BTCUSDT)",
    "budget_usd": "Bütçe miktarı sayı olarak (örnek: 250)"
  }},
  "anlik_ozet": "Maliyet={cost} Anlık varlık takibi sağ panelde aktif."
}}
"""
        if llm_provider == "openai":
            ai_text = await _call_openai_with_retry(openai_client, openai_model_name, prompt)
            ai_text = ai_text.strip()
        else:
            response = await _call_gemini_with_retry(gemini_model, prompt)
            ai_text = response.text.strip()
        
        import json
        import re
        
        final_text = ai_text
        try:
            # JSON formatını güvenli şekilde parse etmek için
            json_match = re.search(r'\{.*\}', ai_text, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                parsed_data = json.loads(json_str)
                
                islem = parsed_data.get("islem_tetikleme", {})
                action = str(islem.get("action", "NONE")).upper()
                sistem_bildirimi = ""
                
                if action in ["BUY", "SELL"]:
                    symbol = str(islem.get("symbol", "")).replace('/', '').upper()
                    try:
                        capital = float(islem.get("budget_usd", 0))
                    except ValueError:
                        capital = 0.0
                        
                    if symbol and capital > 0:
                        try:
                            live_trade_manager.open_position(symbol=symbol, capital=capital, side=action)
                            sistem_bildirimi = f"\n\n**✅ SİSTEM BİLDİRİMİ:** Alpaca tetiklendi! {symbol} için ${capital} tutarında {action} emri piyasaya iletildi."
                        except Exception as trade_err:
                            sistem_bildirimi = f"\n\n**❌ SİSTEM BİLDİRİMİ:** Alpaca emri iletilemedi! Hata: {str(trade_err)}"
                            
                final_text = (
                    f"[REJİM]: {parsed_data.get('rejim')}\n"
                    f"[VADE TERCİHİ]: {parsed_data.get('vade_tercihi')}\n"
                    f"[STRATEJİK DEĞERLENDİRME]: {parsed_data.get('stratejik_degerlendirme')}\n"
                    f"[HIZLI EYLEM KARARI]: {parsed_data.get('hizli_eylem_karari')}\n"
                    f"[İŞLEM TETİKLEME]: {action} {islem.get('symbol', '')} {islem.get('budget_usd', '')}\n"
                    f"[ANLIK ÖZET]: {parsed_data.get('anlik_ozet')}{sistem_bildirimi}"
                )

        except Exception as parse_err:
            logger.error(f"[IDE JSON ERROR] {parse_err}. Raw text: {ai_text}")
            # Fallback to regex if JSON fails
            match = re.search(r'\[EXECUTE_TRADE\]:\s*(BUY|SELL)\s+([A-Za-z0-9/]+)\s+\$?(\d+(?:\.\d+)?)', ai_text, re.IGNORECASE)
            if match:
                action = match.group(1).upper()
                symbol = match.group(2).replace('/', '').upper()
                capital = float(match.group(3))
                try:
                    live_trade_manager.open_position(symbol=symbol, capital=capital, side=action)
                    final_text += f"\n\n**✅ SİSTEM BİLDİRİMİ:** Alpaca tetiklendi! {symbol} için ${capital} tutarında {action} emri piyasaya iletildi."
                except Exception as trade_err:
                    final_text += f"\n\n**❌ SİSTEM BİLDİRİMİ:** Alpaca emri iletilemedi! Hata: {str(trade_err)}"

        return {
            "status": "success",
            "cost": cost,
            "remaining_credits": live_trade_manager.user_credits,
            "result_text": final_text
        }
    except Exception as e:
        logger.error(f"[IDE ERROR] {e}")
        # Hata olursa parayı iade et
        live_trade_manager.user_credits += cost
        raise HTTPException(status_code=500, detail=str(e))


class CustomPromptRequest(BaseModel):
    prompt: str

@router.post("/analyst/custom")
async def trigger_analyst_custom(req: CustomPromptRequest):
    try:
        final_prompt = req.prompt
        
        llm_provider = os.getenv("LLM_PROVIDER", "gemini").lower()
        if llm_provider == "openai":
            openai_model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-6-astra")
            if openai_model_name == "gpt-6-astra":
                api_key = os.getenv("OPENAI_API_KEY_SECONDARY") or os.getenv("OPENAI_API_KEY")
            else:
                api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise Exception("OPENAI_API_KEY eksik.")
            base_url = os.getenv("OPENAI_BASE_URL")
            openai_client = AsyncOpenAI(api_key=api_key, base_url=base_url)
            openai_model_name = os.getenv("OPENAI_MODEL_NAME", "gpt-6-astra")
            try:
                ai_text = await _call_openai_with_retry(openai_client, openai_model_name, final_prompt)
            except Exception as e:
                logger.warning(f"[FALLBACK] OpenAI/Codex hatası ({e}). Gemini modeline geçiliyor...")
                gemini_api_key = os.getenv("GEMINI_API_KEY")
                if not gemini_api_key:
                    raise Exception("OpenAI başarısız oldu ve GEMINI_API_KEY bulunamadı.")
                genai.configure(api_key=gemini_api_key)
                model = genai.GenerativeModel("gemini-1.5-flash")
                response = await _call_gemini_with_retry(model, final_prompt)
                ai_text = response.text
        else:
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise Exception("GEMINI_API_KEY eksik.")
            genai.configure(api_key=api_key)
            model = genai.GenerativeModel("gemini-1.5-flash")
            response = await _call_gemini_with_retry(model, final_prompt)
            ai_text = response.text.strip()
        
        return {"response": ai_text}
    except Exception as e:
        logger.error(f"Analyst Error: {e}")
        return {"response": f"Hata: {str(e)}"}
