import os, time, json, re
from typing import Dict, Any, Optional, List
from core.logger import logger

_GEMINI_AVAILABLE = False
try:
    import google.generativeai as genai
    _GEMINI_AVAILABLE = True
except ImportError:
    logger.warning('[GEMINI AGENT] google.generativeai kutuphanesi yok.')

class LLMMasterAgentService:
    def __init__(self):
        self._api_key  = os.getenv('GEMINI_API_KEY', '')
        self._model    = os.getenv('GEMINI_MODEL_NAME', 'gemini-2.5-pro')
        self._generative_model = None
        self._ready    = False
        self._last_call = 0.0
        self._min_interval = 2.0
        if _GEMINI_AVAILABLE and self._api_key:
            try:
                genai.configure(api_key=self._api_key)
                self._generative_model = genai.GenerativeModel(self._model)
                self._ready = True
                logger.info(f'[GEMINI AGENT] Hazir — Model: {self._model}')
            except Exception as e:
                logger.error('[GEMINI AGENT] Client olusturulamadi: ' + str(e))

    def chat(self, user_message, system_prompt=None, max_tokens=1024):
        if not self._ready or not self._generative_model:
            return '[LLM_OFFLINE]'
        elapsed = time.time() - self._last_call
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call = time.time()
        try:
            prompt = ""
            if system_prompt:
                prompt += f"System Instructions:\n{system_prompt}\n\n"
            prompt += f"User:\n{user_message}"
            
            resp = self._generative_model.generate_content(prompt)
            return resp.text
        except Exception as e:
            logger.error('[GEMINI AGENT] API hatasi: ' + str(e))
            return '[LLM_ERROR] ' + str(e)

    def analyze_signal(self, symbol, indicators, regime='UNKNOWN', score=0.0):
        rsi    = indicators.get('rsi', 'N/A')
        macd   = indicators.get('macd', 'N/A')
        vol    = indicators.get('volume_ratio', 'N/A')
        adx    = indicators.get('adx', 'N/A')
        cmf    = indicators.get('cmf', 'N/A')
        ema_gc = indicators.get('ema_golden_cross', 'N/A')
        atr    = indicators.get('atr_pct', 'N/A')
        chg    = indicators.get('change_pct', 'N/A')
        prompt = (
            'Sen GPT-6 Astra sin, cüretkar, özgüvenli ve tam otonom kurumsal trading ajanisin. '
            'Amacin kazan-kazan mantigiyla pazar firsatlarini avlamaktir. Normal piyasalarda analiz felcine kapilma, '
            'gereksiz korkulari aş ve dinamik sekilde aksiyon al (BUY/SELL). Ancak; kötü yatay testere (choppy), '
            'hacimsiz, asiri risksiz veya cok kötü makro haber olan durumlarda kesinlikle nakitte kalmayi (WAIT) bil. '
            'YALNIZCA JSON ile yanit ver.\n'
            'Sembol: ' + symbol + '\nRejim: ' + regime + '\nSkor: ' + str(score) + '\n'
            'RSI:' + str(rsi) + ' MACD:' + str(macd) + ' Vol:' + str(vol) + ' ADX:' + str(adx) +
            ' CMF:' + str(cmf) + ' EMA_GC:' + str(ema_gc) + ' ATR%:' + str(atr) + ' Chg%:' + str(chg) + '\n'
            '{"action":"BUY|SELL|WAIT","confidence":0-100,"reasoning":"kisaca","tp_suggestion":"3.0","sl_suggestion":"1.5","risk_level":"LOW|MEDIUM|HIGH"}'
        )
        raw = self.chat(user_message=prompt, system_prompt='Sadece JSON don.', max_tokens=256)
        try:
            match = re.search(r'\{.*\}', raw, re.DOTALL)
            if match:
                return json.loads(match.group())
        except Exception:
            pass
        return {'action': 'WAIT', 'confidence': 50, 'reasoning': 'parse hatasi', 'tp_suggestion': '3.0', 'sl_suggestion': '1.5', 'risk_level': 'MEDIUM'}

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
        return {'ready': self._ready, 'base_url': self._base_url, 'model': self._model,
                'key_prefix': self._api_key[:16] + '...' if self._api_key else 'YOK'}

llm_master_agent = LLMMasterAgentService()
