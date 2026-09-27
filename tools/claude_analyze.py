import os
import sys
import argparse
from openai import OpenAI
from dotenv import load_dotenv

def main():
    load_dotenv()
    
    api_key = os.getenv("ANTHROPIC_AUTH_TOKEN")
    base_url = os.getenv("ANTHROPIC_BASE_URL", "https://darkapi.shop/v1")
    model_name = os.getenv("ANTHROPIC_MODEL", "claude-sonnet-5")
    
    try:
        with open("prompt.txt", "r", encoding="utf-8") as f:
            prompt_text = f.read()
    except Exception as e:
        print(f"HATA: prompt.txt okunamadi: {e}")
        return 1
    
    if not api_key:
        print("HATA: ANTHROPIC_AUTH_TOKEN .env dosyasinda bulunamadi.")
        return 1

    try:
        client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        
        # Timeout'lari onlemek icin streaming aktif edildi
        response_stream = client.chat.completions.create(
            max_tokens=4096,
            messages=[
                {
                    "role": "user",
                    "content": prompt_text,
                }
            ],
            model=model_name,
            stream=True
        )
        
        for chunk in response_stream:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                sys.stdout.write(chunk.choices[0].delta.content)
                sys.stdout.flush()
        print() # Sonuna bosluk
        return 0
    except Exception as e:
        sys.stdout.reconfigure(encoding='utf-8')
        print(f"Claude API Hatasi: {e}")
        return 1

if __name__ == "__main__":
    # Konsol encoding sorunlarini onlemek icin
    sys.stdout.reconfigure(encoding='utf-8')
    sys.exit(main())
