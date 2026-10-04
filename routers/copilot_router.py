import json
import asyncio
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import google.generativeai as genai

from services.market_feed.live_stream import live_trade_manager

router = APIRouter(prefix="/api/copilot", tags=["Co-Pilot Chat"])

class CopilotMessage(BaseModel):
    role: str
    content: str

class CopilotRequest(BaseModel):
    messages: List[CopilotMessage]
    model_name: str = "gemini-1.5-flash"
    api_key: Optional[str] = None
    include_context: bool = True

def _build_system_context() -> str:
    # Portfolio statüsünü çek
    bal = live_trade_manager.account_balance
    cash = live_trade_manager.available_cash
    
    positions = []
    for p in live_trade_manager.positions.values():
        if p.status in ["OPEN", "SHADOW_OPEN"]:
            positions.append(f"- {p.symbol}: {p.side} | Giriş: ${p.entry_price:.2f} | Adet: {p.quantity} | PnL: ${p.unrealized_pnl:.2f}")
    
    pos_str = "\n".join(positions) if positions else "Açık pozisyon yok."
    
    return f"""Sen 'Derin Masa'nın süper zeki Yapay Zeka Yardımcı Pilotusun (Co-Pilot).
Görevin: Kullanıcıya kripto, borsa (BIST/NASDAQ) ve genel fon yönetimi konusunda en proaktif, net ve taktiksel tavsiyeleri vermek.
Eğer analiz yaparsan, teknik (RSI, Trend, Hacim) ve temel (Psikoloji, Risk) detayları sentezle.
Cevapların kısa, vurucu ve net olsun. Asla uzun, sıkıcı metinler yazma. Kararlı ol. "Şunu yapmalısın" demekten çekinme.

---
ANLIK KASA VE PORTFÖY DURUMU:
Toplam Kasa: ${bal:.2f}
Boşta (Kullanılabilir) Nakit: ${cash:.2f}

AKTİF POZİSYONLAR:
{pos_str}
---
"""

@router.post("/stream")
async def chat_copilot_stream(req: CopilotRequest):
    import os
    
    try:
        model_name = req.model_name
        if not model_name:
            model_name = "gemini-3.8-flash"
            
        system_prompt = _build_system_context() if req.include_context else None
            
        async def event_generator():
            try:
                if "gemini" in model_name:
                    api_key = req.api_key or os.environ.get("GEMINI_API_KEY")
                    if not api_key:
                        raise Exception("Gemini API Key eksik.")
                        
                    genai.configure(api_key=api_key)
                    model = genai.GenerativeModel(model_name=model_name, system_instruction=system_prompt)
                    
                    formatted_messages = []
                    for m in req.messages:
                        formatted_messages.append({"role": "user" if m.role == "user" else "model", "parts": [m.content]})
                        
                    response = await model.generate_content_async(formatted_messages, stream=True)
                    
                    async for chunk in response:
                        if chunk.text:
                            yield f"data: {json.dumps({'text': chunk.text})}\n\n"
                            await asyncio.sleep(0.01)
                            
                else:
                    # OpenAI / Astra (Pro) fallback
                    from openai import AsyncOpenAI
                    
                    # ai_chat_router.py'deki Pro key veya .env
                    api_key = os.environ.get("OPENAI_API_KEY", "tc_live_fwiknvr71Xjb8pOjcqvTzNDHPpSo-ZgRHzFkFuBX6Nc")
                    base_url = os.environ.get("OPENAI_API_BASE", "https://tokens.deployapp.space/v1")
                    
                    client = AsyncOpenAI(api_key=api_key, base_url=base_url)
                    
                    messages = []
                    if system_prompt:
                        messages.append({"role": "system", "content": system_prompt})
                    
                    for m in req.messages:
                        messages.append({"role": m.role, "content": m.content})
                        
                    response = await client.chat.completions.create(
                        model="cx/gpt-6-astra" if "astra" in model_name else model_name,
                        messages=messages,
                        stream=True,
                        max_tokens=2000
                    )
                    
                    async for chunk in response:
                        if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                            yield f"data: {json.dumps({'text': chunk.choices[0].delta.content})}\n\n"
                            await asyncio.sleep(0.01)

                yield "data: [DONE]\n\n"
            except Exception as e:
                yield f"data: {json.dumps({'error': str(e)})}\n\n"

        return StreamingResponse(event_generator(), media_type="text/event-stream")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
