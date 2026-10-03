import os, time, json, re
from typing import Dict, Any, Optional, List
from core.logger import logger

# --- OpenAI (Astra-6) ---
_OPENAI_AVAILABLE = False
try:
    import openai
    _OPENAI_AVAILABLE = True
except ImportError:
    logger.warning('[LLM AGENT] openai kütüphanesi yok.')

# --- Gemini (Ana Motor) ---
_GEMINI_AVAILABLE = False
try:
    import google.generativeai as genai
    _GEMINI_AVAILABLE = True
except ImportError:
    logger.warning('[GEMINI AGENT] google.generativeai kütüphanesi yok.')

class LLMMasterAgentService:
    def __init__(self):
        # -- OpenAI (Astra-6) --
        self._oai_ready  = False
        self._oai_client = None
        self._oai_key = os.getenv('OPENAI_API_KEY', '')
        self._base_url = os.getenv('OPENAI_API_BASE', 'https://api.openai.com/v1')
        self._model = os.getenv('OPENAI_MODEL_NAME', 'gpt-4o')

        if _OPENAI_AVAILABLE and self._oai_key:
            try:
                self._oai_client = openai.OpenAI(api_key=self._oai_key, base_url=self._base_url, timeout=60.0)
                self._oai_ready = True
                logger.info(f'[LLM AGENT] Astra-6 (OpenAI Proxy) Aktif — Model: {self._model}')
            except Exception as e:
                logger.error(f'[LLM AGENT] OpenAI client oluşturulamadı: {e}')

        # -- Gemini (Yedek/Ana Motor) --
        self._api_key  = os.getenv('GEMINI_API_KEY', '')
        self._model_gemini = os.getenv('GEMINI_MODEL_NAME', 'gemini-3.1-pro-preview')
        self._generative_model = None
        self._gemini_ready  = False

        if _GEMINI_AVAILABLE and self._api_key:
            try:
                genai.configure(api_key=self._api_key)
                self._generative_model = genai.GenerativeModel(self._model_gemini)
                self._gemini_ready = True
                logger.info(f'[LLM AGENT] Yüce Divan (Gemini) Aktif — Model: {self._model_gemini}')
            except Exception as e:
                logger.error('[LLM AGENT] Gemini client oluşturulamadı: ' + str(e))

        self._ready = self._oai_ready or self._gemini_ready
        self._last_call = 0.0
        self._min_interval = 1.0

    def chat(self, user_message, system_prompt=None, max_tokens=1024, engine_preference='auto'):
        if not self._ready:
            return '[LLM_OFFLINE]'

        elapsed = time.time() - self._last_call
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call = time.time()

        # 1. Astra-6 (OpenAI) Denemesi
        if self._oai_ready and self._oai_client and engine_preference in ('auto', 'astra'):
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': user_message})
            try:
                resp = self._oai_client.chat.completions.create(
                    model=self._model,
                    messages=messages,
                    max_tokens=max_tokens
                )
                return resp.choices[0].message.content
            except Exception as e:
                err_msg = str(e).lower()
                if '402' in err_msg or 'balance' in err_msg or 'insufficient' in err_msg or 'quota' in err_msg or '429' in err_msg:
                    logger.warning("[LLM AGENT] Astra-6 Kredisi bitti veya Limit asildi! Yuce Divan Gemini'ye geciliyor...")
                    self._oai_ready = False  # Disable OpenAI for future calls to fail fast to Gemini
                else:
                    logger.error(f'[LLM AGENT] Astra-6 (OpenAI) Hatası: {e}')

        # 2. Yüce Divan (Gemini) Denemesi (Fallback veya Tercihli Gemini Kullanımı)
        if self._gemini_ready and self._generative_model and engine_preference in ('auto', 'gemini') or (engine_preference == 'astra' and not self._oai_ready):
            try:
                prompt = ''
                if system_prompt:
                    prompt += f'System Instructions:\n{system_prompt}\n\n'
                prompt += f'User:\n{user_message}'
                resp = self._generative_model.generate_content(prompt)
                return resp.text
            except Exception as e:
                logger.error('[LLM AGENT] Gemini hatasi: ' + str(e))
                return '[LLM_ERROR] ' + str(e)

        return '[LLM_OFFLINE]'

    def analyze_signal(self, symbol, indicators, regime='UNKNOWN', score=0.0):
        try:
            from services.engine.experience_memory_engine import experience_memory_engine
            past_trades = [t for t in experience_memory_engine.trade_history if t.symbol == symbol]
            past_context = f"Önceki İşlem Sayısı: {len(past_trades)}. "
            if past_trades:
                win_rate = sum(1 for t in past_trades if t.is_win) / len(past_trades) * 100
                past_context += f"Win Rate: %{win_rate:.1f}. "
        except Exception:
            past_context = "Geçmiş işlem verisi yok."

        rsi    = indicators.get('rsi', 'N/A')
        macd   = indicators.get('macd', 'N/A')
        vol    = indicators.get('volume_ratio', 'N/A')
        adx    = indicators.get('adx', 'N/A')
        cmf    = indicators.get('cmf', 'N/A')
        ema_gc = indicators.get('ema_golden_cross', 'N/A')
        atr    = indicators.get('atr_pct', 'N/A')
        chg    = indicators.get('change_pct', 'N/A')
        
        prompt = (
            'Sen Yüce Divan Baş Yargıcısın (Tier-1 Finansal Yapay Zeka). '
            'Aşağıdaki varlık için KARAR vermeden önce kendi içinde bir MÜNAZARA (Debate) yapacaksın.\n'
            'Adım 1: BOĞA (Alıcı) tarafının argümanlarını düşün (Neden alınmalı?).\n'
            'Adım 2: AYI (Satıcı) tarafının argümanlarını düşün (Neden tuzak olabilir, riskler neler?).\n'
            'Adım 3: Geçmiş Hafıza (RAG Context) ile bu argümanları sentezle.\n'
            'Adım 4: Yalnızca JSON formatında nihai kararını ver.\n\n'
            f'Sembol: {symbol} | Rejim: {regime} | Teknik Skor: {score}\n'
            f'Geçmiş Hafıza (RAG): {past_context}\n'
            f'Teknikler -> RSI:{rsi} MACD:{macd} Vol:{vol} ADX:{adx} CMF:{cmf} EMA_GC:{ema_gc} ATR%:{atr} Chg%:{chg}\n\n'
            'DÖNDÜRMEN GEREKEN FORMAT SADECE JSON:\n'
            '{"bull_case":"...", "bear_case":"...", "action":"BUY|SELL|WAIT", "confidence":0-100, "reasoning":"...", "tp_suggestion":"3.0", "sl_suggestion":"1.5", "risk_level":"LOW|MEDIUM|HIGH"}'
        )
        raw = self.chat(user_message=prompt, system_prompt='Sen FinGPT/Astra-6 kalibresinde Tier-1 bir analistsin. Sadece JSON dön.', max_tokens=512, engine_preference='astra')
        try:
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            logger.error(f"[DEBATE ERROR] LLM JSON ayıklanamadı: {e}")
        
        return {'bull_case': '', 'bear_case': '', 'action': 'WAIT', 'confidence': 50, 'reasoning': 'parse hatasi', 'tp_suggestion': '3.0', 'sl_suggestion': '1.5', 'risk_level': 'MEDIUM'}

    def market_commentary(self, symbols_data):
        lines = [str(s.get('symbol')) + ':' + str(s.get('decision','?')) + ' RSI:' + str(s.get('rsi',0)) for s in symbols_data[:8]]
        prompt = 'Asagidaki piyasa verilerine bakarak 3 cumlelik Turkce piyasa yorumu yaz:\n' + '\n'.join(lines)
        return self.chat(user_message=prompt, max_tokens=300, engine_preference='gemini')

    def strategy_advisor(self, trade_history, current_mode):
        wins = [t for t in trade_history if t.get('net_pnl', 0) > 0]
        total_pnl = sum(t.get('net_pnl', 0) for t in trade_history)
        win_rate = (len(wins) / len(trade_history) * 100) if trade_history else 0
        prompt = ('Trading performans: ' + str(len(trade_history)) + ' islem, Win%' + str(round(win_rate,1)) +
                  ', PnL$' + str(round(total_pnl,2)) + ', Mod:' + current_mode +
                  '\nTurkce: 1) Performans 2) Onerilen mod (SNIPER/AGGRESSIVE/NORMAL/TIGHT/CONSERVATIVE) 3) Neden')
        return self.chat(user_message=prompt, max_tokens=256, engine_preference='gemini')

    def is_ready(self):
        return self._ready

    def status(self):
        return {
            'ready':      self._ready,
            'provider':   'Astra-6 (OpenAI)' if getattr(self, '_oai_ready', False) else ('Gemini' if getattr(self, '_gemini_ready', False) else 'OFFLINE'),
            'base_url':   getattr(self, '_base_url', 'gemini') if getattr(self, '_oai_ready', False) else 'gemini',
            'model':      getattr(self, '_model', self._model_gemini) if getattr(self, '_oai_ready', False) else getattr(self, '_model_gemini', ''),
            'key_prefix': (getattr(self, '_oai_key', '')[:20] + '...') if getattr(self, '_oai_key', '') else 'YOK',
        }

llm_master_agent = LLMMasterAgentService()
