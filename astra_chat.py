import urllib.request
import json
import sys
import os

API_KEY = "tc_live_fwiknvr71Xjb8pOjcqvTzNDHPpSo-ZgRHzFkFuBX6Nc"
URL = "https://tokens.deployapp.space/v1/chat/completions"

print("="*60)
print("🚀 GPT-5.6-SOL (TOKEN HOUSE) TERMINAL KÖPRÜSÜ 🚀")
print("- Çıkmak için: 'exit' veya 'quit'")
print("- Dosya okutmak için: '/oku dosya_adi.py' (Örn: /oku main.py)")
print("="*60)

messages = [{"role": "system", "content": "Sen GPT-5.6-Sol modelisin. Uzman bir yazılım mimarı ve trade botu geliştiricisisin. Sana gönderilen kod dosyalarını analiz edip kullanıcıya net çözümler sunacaksın."}]

while True:
    try:
        user_input = input("\nSen: ")
        if user_input.lower() in ['exit', 'quit']:
            print("Kapatılıyor...")
            sys.exit(0)
            
        if not user_input.strip():
            continue

        # DOSYA OKUMA ÖZELLİĞİ (413 Hatasını engellemek için sadece istenen dosya okunur)
        if user_input.startswith("/oku "):
            file_name = user_input.split(" ", 1)[1].strip()
            if os.path.exists(file_name):
                with open(file_name, "r", encoding="utf-8") as f:
                    file_content = f.read()
                msg = f"Kullanıcı şu an '{file_name}' adlı dosyanın içeriğini seninle paylaştı. Lütfen analiz et.\n\nİçerik:\n```python\n{file_content}\n```"
                messages.append({"role": "user", "content": msg})
                print(f"✅ '{file_name}' dosyası başarıyla bota gönderildi. Düşünüyor...")
            else:
                print(f"❌ Hata: '{file_name}' bulunamadı. Tam dosya yolunu veya adını doğru yazdığından emin ol.")
                continue
        else:
            messages.append({"role": "user", "content": user_input})
            print("Bot Düşünüyor...\n")
        
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {API_KEY}"
        }
        
        data = {
            "model": "cx/gpt-6-astra",
            "messages": messages,
            "max_tokens": 2000,
            "stream": False
        }
        
        req = urllib.request.Request(URL, data=json.dumps(data).encode(), headers=headers)
        
        with urllib.request.urlopen(req) as resp:
            raw_response = resp.read().decode('utf-8')
            response_data = json.loads(raw_response)
            reply = response_data['choices'][0]['message']['content']
            
            if not user_input.startswith("/oku "):
                print(f"🤖 Bot:\n{reply}")
            else:
                print(f"🤖 Bot (Dosya Analizi):\n{reply}")
                
            messages.append({"role": "assistant", "content": reply})

    except KeyboardInterrupt:
        print("\nKapatılıyor...")
        sys.exit(0)
    except urllib.error.HTTPError as e:
        if e.code == 413:
            print("\n❌ Hata 413: Gönderilen dosya veya sohbet geçmişi Token House sunucusu için çok büyük! Sohbeti kapatıp yeniden başlatman gerekebilir.")
        else:
            print(f"\n❌ API Hatası: {e.code} - {e.reason}")
    except Exception as e:
        print(f"\n❌ Hata oluştu: {e}")
