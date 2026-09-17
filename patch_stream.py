import os
import re

# 1. Update research_engine.py
with open('services/ai_agent/research_engine.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Add a streaming function
new_stream_method = '''
    def _query_openai_stream(self, prompt: str, system_msg: str = "Sen elit bir kantitatif analist ve trade psikoloğusun. Adın Gölge Zeka. Gelen sorulara profesyonel, doğrudan ve eyleme dökülebilir Türkçe yanıtlar ver."):
        if not self.client:
            yield "Sistem Hatası: OpenAI API Key bulunamadı."
            return
            
        try:
            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": system_msg},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=1000,
                stream=True
            )
            for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    content = chunk.choices[0].delta.content
                    if content:
                        yield content
        except Exception as e:
            logger.error(f"OpenAI API Hatası (Stream): {str(e)}")
            yield f"Üzgünüm, analiz motoru yanıt veremedi: {str(e)}"
'''

# Inject it after _query_openai
target = 'def _query_openai(self, prompt: str'
if '_query_openai_stream' not in code:
    code = code.replace(target, new_stream_method + '\n    ' + target)

with open('services/ai_agent/research_engine.py', 'w', encoding='utf-8') as f:
    f.write(code)

# 2. Update agent_router.py
with open('routers/agent_router.py', 'r', encoding='utf-8') as f:
    router_code = f.read()

# Add StreamingResponse to imports
if 'StreamingResponse' not in router_code:
    router_code = router_code.replace('from fastapi import APIRouter', 'from fastapi import APIRouter\nfrom fastapi.responses import StreamingResponse')

new_endpoint = '''
@router.get("/stream")
async def agent_custom_stream(prompt: str):
    """
    Sohbet penceresi için Streaming (Akış) endpoint'i.
    """
    def event_generator():
        try:
            # Sadece LLM kısmını stream et.
            for chunk in agent_engine._query_openai_stream(prompt=prompt):
                # SSE format: data: {text}\n\n
                # Encode newlines so they don't break SSE protocol
                safe_chunk = chunk.replace('\\n', '<br>')
                yield f"data: {safe_chunk}\\n\\n"
        except Exception as e:
            yield f"data: Hata: {str(e)}\\n\\n"
        yield "data: [DONE]\\n\\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
'''

if '/stream' not in router_code:
    router_code += '\n' + new_endpoint

with open('routers/agent_router.py', 'w', encoding='utf-8') as f:
    f.write(router_code)

print("Backend patched for streaming.")
