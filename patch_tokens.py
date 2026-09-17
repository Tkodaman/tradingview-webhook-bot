import os

with open('services/ai_agent/research_engine.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Modify _query_openai to return tokens too
old_query = '''            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI API Hatası: {str(e)}")
            return f"Üzgünüm, analiz motoru yanıt veremedi: {str(e)}"'''
new_query = '''            tokens_used = response.usage.total_tokens if response.usage else 0
            return response.choices[0].message.content, tokens_used
        except Exception as e:
            logger.error(f"OpenAI API Hatası: {str(e)}")
            return f"Üzgünüm, analiz motoru yanıt veremedi: {str(e)}", 0'''
code = code.replace(old_query, new_query)

# Modify ask_custom_analyst to capture tokens and inject to structured_data
old_ask = '''            # OpenAI isteği
            llm_response = self._query_openai(prompt=req.prompt, system_msg=system_msg)
            
            return AgentResponse(
                agent_name="Gölge Zeka (LLM Mode)",
                skill_used="Dynamic ChatGPT Analyst",
                mode="LIVE_LLM",
                title=f"Analiz: {req.symbol if req.symbol else 'Genel Piyasa'}",
                summary="Canlı LLM yanıtı oluşturuldu.",
                structured_data={"provider": "OpenAI/Astra"},'''
new_ask = '''            # OpenAI isteği
            llm_response, tokens = self._query_openai(prompt=req.prompt, system_msg=system_msg)
            
            return AgentResponse(
                agent_name="Gölge Zeka (LLM Mode)",
                skill_used="Dynamic ChatGPT Analyst",
                mode="LIVE_LLM",
                title=f"Analiz: {req.symbol if req.symbol else 'Genel Piyasa'}",
                summary="Canlı LLM yanıtı oluşturuldu.",
                structured_data={"provider": "OpenAI/Astra", "tokens_used": tokens},'''
code = code.replace(old_ask, new_ask)

with open('services/ai_agent/research_engine.py', 'w', encoding='utf-8') as f:
    f.write(code)
print('Tokens logic added')
