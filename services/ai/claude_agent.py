import os, time, json, re
from typing import Dict, Any, Optional, List
from core.logger import logger

_OPENAI_AVAILABLE = False
try:
    from openai import OpenAI
    _OPENAI_AVAILABLE = True
except ImportError:
    logger.warning('[CLAUDE AGENT] openai kutuphanesi yok.')

class ClaudeAgentService:
    def __init__(self):
        self._api_key  = os.getenv('ANTHROPIC_AUTH_TOKEN', '')
        self._base_url = os.getenv('ANTHROPIC_BASE_URL', 'https://darkapi.shop/v1')
        self._model    = os.getenv('ANTHROPIC_MODEL', 'claude-sonnet-5')
        self._client   = None
        self._ready    = False
        self._last_call = 0.0
        self._min_interval = 1.0
        if _OPENAI_AVAILABLE and self._api_key:
            try:
                self._client = OpenAI(api_key=self._api_key, base_url=self._base_url)
                self._ready = True
                logger.info('[CLAUDE AGENT] Hazir (OpenAI Uyumlu) — ' + self._base_url)
            except Exception as e:
                logger.error('[CLAUDE AGENT] Client olusturulamadi: ' + str(e))

    def chat(self, user_message, system_prompt=None, max_tokens=1024):
        if not self._ready or not self._client:
            return '[CLAUDE_OFFLINE]'
        elapsed = time.time() - self._last_call
        if elapsed < self._min_interval:
            time.sleep(self._min_interval - elapsed)
        self._last_call = time.time()
        try:
            messages = []
            if system_prompt:
                messages.append({'role': 'system', 'content': system_prompt})
            messages.append({'role': 'user', 'content': user_message})
            
            resp = self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                max_tokens=max_tokens
            )
            return resp.choices[0].message.content
        except Exception as e:
            logger.error('[CLAUDE AGENT] API hatasi: ' + str(e))
            return '[CLAUDE_ERROR] ' + str(e)

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

claude_agent = ClaudeAgentService()
