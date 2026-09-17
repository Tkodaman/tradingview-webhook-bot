import re

with open('services/ai_agent/research_engine.py', 'r', encoding='utf-8') as f:
    code = f.read()

new_stream_method = '''
    def _query_openai_stream(self, prompt: str, system_msg: str = "Sen elit bir kantitatif analist ve trade psikoloğusun. Adın Gölge Zeka. Gelen sorulara profesyonel, doğrudan ve eyleme dökülebilir Türkçe yanıtlar ver."):
        if not self.client:
            yield "Sistem Hatası: OpenAI API Key bulunamadı."
            return
            
        import time
        max_retries = 3
        
        for attempt in range(max_retries):
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
                return  # Basarili olursa cik
            except Exception as e:
                err_str = str(e).lower()
                # 503 veya timeout hatalarinda tekrar dene
                if "503" in err_str or "temporarily unavailable" in err_str or "overloaded" in err_str:
                    if attempt < max_retries - 1:
                        yield f"*(Sunucu yoğun, {attempt+1}. kez tekrar deneniyor...)*\\n"
                        time.sleep(2)
                        continue
                
                logger.error(f"OpenAI API Hatası (Stream): {str(e)}")
                yield f"\\nÜzgünüm, analiz motoru yanıt veremedi: {str(e)}"
                return
'''

# Find the old _query_openai_stream and replace it
pattern = r'def _query_openai_stream\(self, prompt: str,.*?(?=def _query_openai\(self)'
code = re.sub(pattern, new_stream_method.strip() + '\n\n    ', code, flags=re.DOTALL)

with open('services/ai_agent/research_engine.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Added retry mechanism to streaming endpoint.")
