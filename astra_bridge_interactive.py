import requests
import json
import sys

def interactive_bridge():
    url = "https://tokens.deployapp.space/v1/chat/completions"
    headers = {
        "Content-Type": "application/json",
        "Authorization": "Bearer tc_live_5hcA1wcFFuWbFJ-4IBkeQ1abwTqLHIONAmu4IN6zmNw"
    }
    
    messages = [
        {"role": "system", "content": "You are Astra 6. Answer the user's queries."}
    ]
    
    print("==================================================")
    print(" ASTRA 6 KÖPRÜSÜ AKTİF ")
    print(" (Çıkmak için 'exit' veya 'çıkış' yazın)")
    print("==================================================\n")
    
    while True:
        try:
            prompt = input("Sen: ")
            if prompt.lower() in ["exit", "çıkış", "quit"]:
                print("Astra 6 bağlantısı kapatılıyor...")
                break
                
            if not prompt.strip():
                continue
                
            messages.append({"role": "user", "content": prompt})
            
            data = {
                "model": "cx/gpt-6-astra",
                "messages": messages,
                "temperature": 0.7,
                "stream": True
            }
            
            print("Astra 6: ", end="", flush=True)
            
            response = requests.post(url, headers=headers, json=data, stream=True, timeout=120)
            
            if response.status_code == 200:
                full_response = ""
                for line in response.iter_lines():
                    if line:
                        line = line.decode('utf-8')
                        if line.startswith("data: "):
                            json_str = line[6:]
                            if json_str.strip() == "[DONE]":
                                break
                            try:
                                chunk = json.loads(json_str)
                                if "choices" in chunk and len(chunk["choices"]) > 0:
                                    delta = chunk["choices"][0].get("delta", {})
                                    if "content" in delta:
                                        content = delta["content"]
                                        print(content, end="", flush=True)
                                        full_response += content
                            except json.JSONDecodeError:
                                pass
                print("\n")
                messages.append({"role": "assistant", "content": full_response})
            else:
                print(f"\n[HATA] API {response.status_code} döndürdü. Detay: {response.text[:200]}\n")
                
        except requests.exceptions.Timeout:
            print("\n[HATA] Astra 6 sunucusu yanıt vermedi (Timeout). Lütfen tekrar deneyin.\n")
        except KeyboardInterrupt:
            print("\nBağlantı kapatılıyor...")
            break
        except Exception as e:
            print(f"\n[HATA] Beklenmeyen bir sorun oluştu: {e}\n")

if __name__ == "__main__":
    interactive_bridge()
