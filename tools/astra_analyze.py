"""Direct Astra 6 backend analysis CLI.

This command uses the project's OpenAI-compatible backend connection, not VS Code
Copilot credits. It performs analysis only and never routes broker orders.
"""
from __future__ import annotations

import argparse
import os
import sys

from dotenv import load_dotenv
from openai import OpenAI


SYSTEM_PROMPT = """Sen Astra 6 Trading Analyst'sin.
Yalnızca analiz yap; emir açma, kapatma veya LIVE moda geçiş önerme.
Gerçek veri verilmediyse bunu açıkça belirt.
Yanıtı Türkçe ve şu formatta ver:
Durum, Kanıt, Risk, Aksiyon, Doğrulama.
Kanıt yetersizse NO-TRADE de.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a direct gpt-6-astra backend analysis")
    parser.add_argument("prompt", nargs="+", help="Analysis request")
    args = parser.parse_args()

    load_dotenv(override=True)
    provider = os.getenv("LLM_PROVIDER", "openai").lower()
    model = os.getenv("OPENAI_MODEL_NAME", "gpt-6-astra")
    base_url = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
    api_key = os.getenv("OPENAI_API_KEY_SECONDARY") or os.getenv("OPENAI_API_KEY")

    if provider != "openai":
        print(f"LLM_PROVIDER=openai değil: {provider}. Astra backend çağrısı durduruldu.", file=sys.stderr)
        return 2
    if not api_key:
        print("OpenAI uyumlu API key eksik.", file=sys.stderr)
        return 2

    client = OpenAI(api_key=api_key, base_url=base_url, timeout=45.0)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": " ".join(args.prompt)},
        ],
        temperature=0.2,
        max_tokens=1200,
    )

    print(response.choices[0].message.content or "Boş yanıt.")
    if response.usage:
        print(
            "\n[backend-usage] model={} prompt_tokens={} completion_tokens={} total_tokens={}".format(
                response.model,
                response.usage.prompt_tokens,
                response.usage.completion_tokens,
                response.usage.total_tokens,
            )
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
