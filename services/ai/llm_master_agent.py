import os, time, json, re
from typing import Dict, Any, Optional, List
from core.logger import logger

# --- Gemini (Ana Motor) ---
_GEMINI_AVAILABLE = False
try:
    import google.generativeai as genai
    _GEMINI_AVAILABLE = True
except ImportError:
    logger.warning('[GEMINI AGENT] google.generativeai kutuphanesi yok.')

class LLMMasterAgentService:
    """
    Gemini 2.5 Pro üzerinden çalışır (Ana Yüce Divan Motoru).
    GEMINI_API_KEY / GEMINI_MODEL_NAME .env'den okunur.
    """

    def __init__(self):
        # KUSURSUZ İNFAZ: OpenAI (tokens.deployapp.space) bakiyesi tükendi. (402 Insufficient Balance)
        # KULLANICI TALEBİ: "Astra 6 model token bittiğinde tüm sistemi Gemini 2.5 Pro'ya geçir."
        
        self._oai_ready  = False
        self._oai_client = None

        # -- Gemini (Birincil Yeni Motor) --
        self._api_key  = os.getenv('GEMINI_API_KEY', '')
        self._model_gemini = os.getenv('GEMINI_MODEL_NAME', 'gemini-3.1-pro-preview')
        self._generative_model = None
        self._gemini_ready  = False

        if _GEMINI_AVAILABLE and self._api_key:
            try:
                genai.configure(api_key=self._api_key)
                self._generative_model = genai.GenerativeModel(self._model_gemini)
                self._gemini_ready = True
                logger.info(f'[LLM AGENT] Yüce Divan Yeni Çekirdek (Gemini) Aktif — Model: {self._model_gemini}')
            except Exception as e:
                logger.error('[LLM AGENT] Gemini client olusturulamadi: ' + str(e))

        self._ready        = self._gemini_ready
        self._last_call    = 0.0
        self._min_interval = 1.5

    def chat(self, user_message, system_prompt=None, max_tokens=1024):
        """Birincil: Gemini 2.5 Pro"""
        if not self._ready:
            return '[LLM_OFFLINE]'

        elapsed = time.time() - self._last_call
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call = time.time()

        if self._gemini_ready and self._generative_model:
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
        # 1. RAG Hafızasını Çek (Eski İşlem Tecrübeleri)
        try:
            from services.engine.experience_memory_engine import experience_memory_engine
            # İlgili sembole ait eski hataları/başarıları çek
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
        
        # 2. Multi-Agent Debate Prompt (Boğa vs Ayı Münazarası)
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
        raw = self.chat(user_message=prompt, system_prompt='Sen FinGPT/Astra-6 kalibresinde Tier-1 bir analistsin. Sadece JSON dön.', max_tokens=512)
        try:
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception as e:
            logger.error(f"[DEBATE ERROR] LLM JSON ayıklanamadı: {e}")
            pass
        return {'bull_case': '', 'bear_case': '', 'action': 'WAIT', 'confidence': 50, 'reasoning': 'parse hatasi', 'tp_suggestion': '3.0', 'sl_suggestion': '1.5', 'risk_level': 'MEDIUM'}

    def market_commentary(self, symbols_data):
        lines = [str(s.get('symbol')) + ':' + str(s.get('decision','?')) + ' RSI:' + str(s.get('rsi',0)) for s in symbols_data[:8]]
        prompt = 'Asagidaki piyasa verilerine bakarak 3 cumlelik Turkce piyasa yorumu yaz:\n' + '\n'.join(lines)
        return self.chat(user_message=prompt, max_tokens=300)

    def strategy_advisor(self, trade_history, current_mode):
        wins = [t for t in trade_history if t.get('net_pnl', 0) > 0]
        total_pnl = sum(t.get('net_pnl', 0) for t in trade_history)
        win_rate = (len(wins) / len(trade_history) * 100) if trade_history else 0
        prompt = ('Trading performans: ' + str(len(trade_history)) + ' islem, Win%' + str(round(win_rate,1)) +
                  ', PnL$' + str(round(total_pnl,2)) + ', Mod:' + current_mode +
                  '\nTurkce: 1) Performans 2) Onerilen mod (SNIPER/AGGRESSIVE/NORMAL/TIGHT/CONSERVATIVE) 3) Neden')
        return self.chat(user_message=prompt, max_tokens=256)

    def is_ready(self):
        return self._ready

    def status(self):
        return {
            'ready':      self._ready,
            'provider':   'OpenAI-compat' if self._oai_ready else ('Gemini' if self._gemini_ready else 'OFFLINE'),
            'base_url':   self._base_url if self._oai_ready else 'gemini',
            'model':      self._model if self._oai_ready else self._model_gemini,
            'key_prefix': (self._oai_key[:20] + '...') if self._oai_key else 'YOK',
        }


llm_master_agent = LLMMasterAgentService()
