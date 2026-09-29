from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import urllib.request
import json
from typing import List

router = APIRouter(prefix="/api/chat", tags=["AI Chat"])

# astra_chat.py'den alınan Token House API konfigürasyonu
API_KEY = "tc_live_fwiknvr71Xjb8pOjcqvTzNDHPpSo-ZgRHzFkFuBX6Nc"
URL = "https://tokens.deployapp.space/v1/chat/completions"

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    messages: List[ChatMessage]

@router.post("/")
async def chat_with_astra(req: ChatRequest):
    """
    Ana Trade Botu üzerinden GPT-5.6-Sol (Astra) modeline sorgu atılmasını sağlayan endpoint.
    Frontend'den veya diğer servislerden bu uç noktaya mesaj geçmişi gönderilerek AI yanıtı alınabilir.
    """
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        
        # Pydantic objelerinden dict listesi oluştur
        formatted_messages = [{"role": m.role, "content": m.content} for m in req.messages]
        
        # Eğer system prompt yoksa, otomatik ekle
        if not any(m["role"] == "system" for m in formatted_messages):
            formatted_messages.insert(0, {
                "role": "system", 
                "content": "Sen GPT-5.6-Sol modelisin. Uzman bir yazılım mimarı ve trade botu geliştiricisisin."
            })
        
        data = {
            "model": "cx/gpt-6-astra",
            "messages": formatted_messages,
            "max_tokens": 2000,
            "stream": False
        }
        
        request_obj = urllib.request.Request(URL, data=json.dumps(data).encode(), headers=headers)
        
        with urllib.request.urlopen(request_obj) as resp:
            raw_response = resp.read().decode('utf-8')
            response_data = json.loads(raw_response)
            reply = response_data['choices'][0]['message']['content']
            return {"reply": reply}
            
    except urllib.error.HTTPError as e:
        raise HTTPException(status_code=e.code, detail=f"API Hatası: {e.reason}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
