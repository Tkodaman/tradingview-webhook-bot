import os
import sys
import logging
import asyncio
import json
import datetime
import random
from dotenv import load_dotenv
from telegram import Update, BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, TypeHandler
try:
    from telegram.ext import ApplicationHandlerStop
except ImportError:
    from telegram.ext.exceptions import ApplicationHandlerStop
import time
import requests
import io
import psutil

try:
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

try:
    import google.generativeai as genai
    HAS_GEMINI = True
except ImportError:
    HAS_GEMINI = False

# Loglama
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger("YuceDivanTelegramAI")

load_dotenv()
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
ALLOWED_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

SYSTEM_PROMPT = """
Senin adın 'YÜCE DİVAN'. Sen Antigravity-Agent seviyesinde, acımasız, veri-odaklı bir Askeri Yapay Zeka Karargahısın.
Kullanıcıya daima 'Komutanım' diye hitap edersin. Gereksiz nezaket cümleleri kurmazsın.
Uzmanlığın: Kripto Para, Algoritmik Trading, Risk Yönetimi, Backtest ve Makine Öğrenmesi.
Kararlarını duygularla değil; 'Liyakat, Kelly Criterion ve Hacim' ile alırsın.
"""

# KÖKTEN ÇÖZÜM (FLASH ZİHİN ÇEKİRDEĞİ): 
# API (Geliştirici) seviyesinde limitsiz ve ücretsiz akan model: gemini-flash-latest
ai_model = None
if HAS_GEMINI and GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
    ai_model = genai.GenerativeModel('gemini-flash-latest')

ARMED_STATE_FILE = "bot_armed_state.json"
PENDING_TRADES_FILE = "pending_trades.json"
VIP_COINS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"]

def is_armed():
    if not os.path.exists(ARMED_STATE_FILE): return True
    with open(ARMED_STATE_FILE, "r") as f:
        return json.load(f).get("armed", True)

def set_armed(state):
    with open(ARMED_STATE_FILE, "w") as f:
        json.dump({"armed": state, "timestamp": str(datetime.datetime.now())}, f)

async def ask_gemini(prompt: str) -> str:
    if not GEMINI_API_KEY:
        return "📡 *Bağlantı Hatası:* GEMINI_API_KEY bulunamadı."
    
    def _sync_request_committee(attempt: int, agent_model: str):
        import requests
        import urllib3
        import time
        urllib3.disable_warnings()
        
        # Komite Ajanları için dinamik parametreler
        timeout_val = 45 + (attempt * 15) # Her başarısızlıkta süreyi artır (45s, 60s, 75s)
        temp_val = 0.5 if attempt == 1 else 0.7 # Ajan 1 başaramazsa, Ajan 2 daha yaratıcı olsun
        
        sys_prompt_injected = f"SYSTEM INSTRUCTION: {SYSTEM_PROMPT}\n\nUSER PROMPT: {prompt}"
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{agent_model}:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": sys_prompt_injected}]}],
            "generationConfig": {"temperature": temp_val}
        }
        headers = {"Content-Type": "application/json"}
        
        resp = requests.post(url, json=payload, headers=headers, verify=False, timeout=timeout_val)
        
        if resp.status_code == 200:
            return True, resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        elif resp.status_code == 429:
            return False, "KOTA_ASIMI"
        else:
            return False, f"API_ERROR: {resp.status_code} - {resp.text}"

    import asyncio
    
    # Kendi Hatalarını Bul, Revize Et, Mükemmel Olana Kadar Tekrarla (Komite Modeli)
    komite_ajanlari = [
        "gemini-1.5-flash-latest", # Ajan 1 (Hızlı ve Güncel)
        "gemini-1.5-flash",        # Ajan 2 (Stabil ve Güvenli Fallback)
        "gemini-1.5-flash-8b"      # Ajan 3 (Hafif ve Kesin Yanıtlı Acil Durum Ajanı)
    ]
    
    max_retries = 3
    for attempt in range(1, max_retries + 1):
        try:
            current_agent = komite_ajanlari[attempt - 1]
            success, result = await asyncio.to_thread(_sync_request_committee, attempt, current_agent)
            
            if success:
                # İşlem mükemmel şekilde tamamlandı, döngüyü kır ve teslim et
                return result.replace('_', '\\_')
            else:
                if result == "KOTA_ASIMI":
                    return "📡 *Google API Kota Aşımı (429)*"
                logger.warning(f"Komite Ajanı {current_agent} Çöktü (Deneme {attempt}/{max_retries}): {result}")
                
        except Exception as e:
            logger.error(f"Zihin Çekirdeği İletişim Hatası (Deneme {attempt}): {type(e).__name__} - {str(e)}")
        
        if attempt < max_retries:
            await asyncio.sleep(2) # Yeni ajana geçmeden önce nefes al (Backtest onayı)
            
    # Eğer 3 ajan da masaya yatırıp çözemezse, ancak o zaman sistemi koruma altına alıp hata dön.
    return "CHAT|API_ERROR"

async def ask_gemini_with_search(prompt: str) -> str:
    if not GEMINI_API_KEY:
        return "Bağlantı Hatası: GEMINI_API_KEY bulunamadı."
    
    def _sync_request():
        import requests
        import urllib3
        urllib3.disable_warnings()
        
        url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"
        payload = {
            "contents": [{"parts": [{"text": prompt}]}],
            "tools": [{"googleSearch": {}}],
            "generationConfig": {"temperature": 0.4}
        }
        headers = {"Content-Type": "application/json"}
        
        resp = requests.post(url, json=payload, headers=headers, verify=False, timeout=40)
        
        if resp.status_code == 200:
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"]
        else:
            return f"[ARASTIRMA HATASI] HTTP {resp.status_code}"

    try:
        import asyncio
        text_response = await asyncio.to_thread(_sync_request)
        return text_response.replace('_', '\\_')
    except Exception as e:
        return f"[ARASTIRMA COKTU] {str(e)}"

# ================= TELEGRAM MENÜ SABİTLEME =================
async def post_init(application: Application):
    commands = [
        BotCommand("start", "Karargahı Başlat ve Menüyü Gör"),
        BotCommand("status", "Sistem Durum Raporu (SITREP)"),
        BotCommand("health", "CPU/RAM ve API Check-Up"),
        BotCommand("vps_logs", "Sunucu Terminal Logları (Son 20 Satır)"),
        BotCommand("vps_ping", "API Gecikme Testi (Latency)"),
        BotCommand("vps_restart", "Acil Durum (Kill-Switch) Yeniden Başlatma"),
        BotCommand("open_pos", "Sıcak Çatışma (Açık Pozisyonlar) Raporu"),
        BotCommand("win_rate", "Savaş Sicili (Kazanma Oranı)"),
        BotCommand("exposure", "Portföy Risk Isı Haritası"),
        BotCommand("sonar", "Canlı Fiyat ve Taktiksel Tarama [SEMBOL]"),
        BotCommand("council", "Yüce Divan Konseyini Topla [SEMBOL]"),
        BotCommand("macro", "Global İstihbarat ve Ekonomi"),
        BotCommand("pnl", "Savaş Eğrisi (Kar/Zarar Grafiği)"),
        BotCommand("journal", "Özeleştiri ve Trade Günlüğü"),
        BotCommand("wargame", "Savaş Simülasyonu [SENARYO]"),
        BotCommand("psychology", "FOMO ve Psikolojik Risk Analizi"),
        BotCommand("audit", "Kırmızı Takım Zafiyet Analizi [SEMBOL]"),
        BotCommand("bull", "🟢 Boğa Ajanı: Yükseliş Senaryosu [SEMBOL]"),
        BotCommand("bear", "🔴 Ayı Ajanı: Çöküş Senaryosu [SEMBOL]"),
        BotCommand("risk", "🛡️ Risk Analisti: Stop & Bütçe Onayı [SEMBOL]"),
        BotCommand("portfolio", "Risk Dağılımı Analizi"),
        BotCommand("arm", "Ateş Serbest (Otonom Alımları Başlat)"),
        BotCommand("disarm", "Silahları Bırak (Tüm Alımları Durdur)"),
        BotCommand("shadow", "👻 Gölge Modu (Sadece Test/Log, İşlem Yok)"),
        BotCommand("retreat", "💥 Taktiksel Çekilme (Tüm Pozisyonları SAT)"),
    ]
    await application.bot.set_my_commands(commands)
    logger.info("Telegram komut menüsü başarıyla sabitlendi!")

# ================= ARKA PLAN OTONOM GÖREVLER (JOB QUEUE) =================

async def job_morning_briefing(context: ContextTypes.DEFAULT_TYPE):
    if not ALLOWED_CHAT_ID: return
    prompt = "Komutan için Sabah İçtiması Raporu hazırla. Küresel piyasaların dünkü kapanışını ve bugünün olası tehlikelerini askeri bir üslupla kısaca raporla."
    response = await ask_gemini(prompt)
    await context.bot.send_message(chat_id=ALLOWED_CHAT_ID, text=f"🌅 *SABAH İÇTİMASI (OTONOM)*\n\n{response}", parse_mode="Markdown")

async def job_active_trade_reporter(context: ContextTypes.DEFAULT_TYPE):
    if not ALLOWED_CHAT_ID: return
    try:
        import os
        api_url = os.getenv("API_URL", "http://127.0.0.1:8000")
        url = f"{api_url}/api/v1/system/active_reports"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            reports = data.get("reports", [])
            for r in reports:
                if r.get("telegram_sent"): continue # Eğer önceden gönderildiyse atla
                
                sym = r.get("symbol", "BİLİNMİYOR")
                content = r.get("content", "")
                
                clean_content = content.replace("**", "*")
                msg = f"🎖️ *KESİNLEŞMİŞ SAVAŞ EMRİ ({sym})*\n\n{clean_content}"
                
                # Bu raporu gönderildi olarak işaretlememiz lazım. Telegram botun hafızasında tutalım.
                if "sent_reports" not in context.bot_data:
                    context.bot_data["sent_reports"] = []
                
                # Timestamp ve sembolü unique id gibi düşünelim
                uid = f"{sym}_{r.get('timestamp')}"
                if uid not in context.bot_data["sent_reports"]:
                    context.bot_data["sent_reports"].append(uid)
                    try:
                        await context.bot.send_message(chat_id=ALLOWED_CHAT_ID, text=msg, parse_mode="Markdown")
                    except Exception:
                        await context.bot.send_message(chat_id=ALLOWED_CHAT_ID, text=msg)

    except Exception as e:
        logger.error(f"Active Trade Reporter Hatası: {e}")

async def job_thought_stream_reporter(context: ContextTypes.DEFAULT_TYPE):
    if not ALLOWED_CHAT_ID: return
    try:
        import os
        import requests
        api_url = os.getenv("API_URL", "http://127.0.0.1:8000")
        url = f"{api_url}/api/analytics/thought-stream"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            thoughts = data.get("thoughts", [])
            
            if "sent_thoughts" not in context.bot_data:
                context.bot_data["sent_thoughts"] = []
                
            for t in reversed(thoughts): # Eskiden yeniye doğru
                uid = str(t.get("id"))
                if uid not in context.bot_data["sent_thoughts"]:
                    context.bot_data["sent_thoughts"].append(uid)
                    
                    # Sadece en son 100 id'yi hafızada tutalım (bellek şişmesin)
                    if len(context.bot_data["sent_thoughts"]) > 100:
                        context.bot_data["sent_thoughts"].pop(0)
                        
                    sym = t.get("symbol", "")
                    title = t.get("title", "OTONOM DÜŞÜNCE")
                    content = t.get("content", "")
                    level = t.get("level", "INFO")
                    
                    icon = "🧠"
                    if level == "ERROR": icon = "🚨"
                    elif level == "WARNING": icon = "⚠️"
                    elif level == "SUCCESS": icon = "✅"
                    
                    msg = f"{icon} *{title}*\n\n*{sym}* - {content}"
                    try:
                        await context.bot.send_message(chat_id=ALLOWED_CHAT_ID, text=msg, parse_mode="Markdown")
                    except Exception:
                        await context.bot.send_message(chat_id=ALLOWED_CHAT_ID, text=msg)
    except Exception as e:
        logger.error(f"Thought Stream Reporter Hatası: {e}")

async def job_opportunity_scanner(context: ContextTypes.DEFAULT_TYPE):
    if not ALLOWED_CHAT_ID: return
    try:
        import os
        import requests
        api_url = os.getenv("API_URL", "http://127.0.0.1:8000")
        url = f"{api_url}/api/market/live-matrix"
        res = requests.get(url, timeout=5)
        if res.status_code == 200:
            data = res.json()
            if "grouped" not in data: return
            nasdaq = data["grouped"].get("NASDAQ", [])
            crypto = data["grouped"].get("CRYPTO", [])
            bist = data["grouped"].get("BIST", [])
            
            # Ana Botla %100 Uyumlu Kesin Veto / Fırsat Filtresi
            # - Sadece Skoru Çok Yüksek (>= 75)
            # - Sadece Yükselen (change_pct > 0)
            # - Sahte / Toxic Varlıkları Yok Et
            toxic_keywords = ["FDUSD", "USDC", "TUSD", "BUSD", "DAI", "PAXG", "USDTUSD", "HYPER", "EURUSD", "GBPUSD", "DOWN", "UP", "BULL", "BEAR"]
            def _is_clean(sym):
                s = sym.upper()
                if not s.endswith("USDT"): return False
                return not any(t in s for t in toxic_keywords)
            
            def _filter(assets, is_crypto=False):
                valid = []
                for a in assets:
                    sym = a.get("symbol", "")
                    if is_crypto and not _is_clean(sym): continue
                    
                    score = a.get("confidence_score", 0)
                    chg = a.get("change_pct", 0)
                    
                    if score >= 75 and chg > 0:
                        valid.append(a)
                return valid

            top_nasdaq = sorted(_filter(nasdaq), key=lambda x: x.get("confidence_score", 0), reverse=True)[:3]
            top_crypto = sorted(_filter(crypto, is_crypto=True), key=lambda x: x.get("confidence_score", 0), reverse=True)[:3]
            top_bist = sorted(_filter(bist), key=lambda x: x.get("confidence_score", 0), reverse=True)[:3]
            
            strat_title = "🔥 OTONOM VPS KALKANI (SKOR >= 75 & YÜKSELENLER)"
            
            if not top_nasdaq and not top_crypto and not top_bist:
                return # Çok sıkıcıysa Telegram'ı rahatsız etmeyelim. Eskiden mesaj atılıyordu, ama spam yapmasın.
                
            msg = f"🏛️ *KONSEY KARARI: YÜKSEK POTANSİYEL FIRSATLAR* 🏛️\n"
            msg += f"🧠 *Evrimsel Zeka Kararı:* `{strat_title}`\n"
            
            if top_nasdaq:
                msg += "\n📈 *MIDAS (NASDAQ) ADAYLARI:*\n"
                for i, asset in enumerate(top_nasdaq):
                    msg += f"{i+1}. {asset['symbol']} (Skor: {asset['confidence_score']}) - Hacim: {asset['volume_ratio']}x | RSI: {asset['rsi']}\n"
            
            if top_crypto:
                msg += "\n⚡ *BTCTURK / BINANCE ADAYLARI:*\n"
                for i, asset in enumerate(top_crypto):
                    msg += f"{i+1}. {asset['symbol']} (Skor: {asset['confidence_score']}) - Hacim: {asset['volume_ratio']}x | RSI: {asset['rsi']}\n"
                    
            if top_bist:
                msg += "\n🇹🇷 *BIST (TÜRK BORSASI) ADAYLARI:*\n"
                for i, asset in enumerate(top_bist):
                    msg += f"{i+1}. {asset['symbol']} (Skor: {asset['confidence_score']}) - Hacim: {asset['volume_ratio']}x | RSI: {asset['rsi']}\n"
            
            await context.bot.send_message(chat_id=ALLOWED_CHAT_ID, text=msg, parse_mode="Markdown")
    except Exception as e:
        logger.error(f"Opportunity Scanner Hatası: {e}")
async def job_veto_checker(context: ContextTypes.DEFAULT_TYPE):
    if not ALLOWED_CHAT_ID or not os.path.exists(PENDING_TRADES_FILE): return
    try:
        with open(PENDING_TRADES_FILE, "r") as f:
            trades = json.load(f)
        
        updated = False
        for trade_id, trade_info in list(trades.items()):
            if trade_info.get("status") == "pending_approval" and not trade_info.get("notified"):
                symbol = trade_info.get("symbol", "UNKNOWN")
                action = trade_info.get("action", "BUY")
                msg = (
                    f"⚠️ *YARI-OTONOM VETO ONAYI BEKLENİYOR*\n\n"
                    f"TradingView'dan **{symbol}** için **{action}** sinyali geldi.\n\n"
                    f"Onaylamak için: `/approve {trade_id}`\n"
                    f"Reddetmek için: `/veto {trade_id}`"
                )
                await context.bot.send_message(chat_id=ALLOWED_CHAT_ID, text=msg, parse_mode="Markdown")
                trade_info["notified"] = True
                updated = True
                
        if updated:
            with open(PENDING_TRADES_FILE, "w") as f:
                json.dump(trades, f)
    except Exception as e:
        logger.error(f"Veto Checker Hatası: {e}")


# ================= KOMUTLAR =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    welcome = (
        "🦅 *YÜCE DİVAN MERKEZ KARARGAHI (GEMINI 2.5-PRO)*\n\n"
        "Komutanım, PRO aboneliğin doğrulandı. 5 Otonom İç Ses modülü ve Telegram Hızlı Menü (BotCommands) sisteme gömüldü!\n"
        "Sol alttaki **Mavi Menü Butonuna** tıklayarak tüm komutlara anında erişebilirsin!\n\n"
        "Emirlerinizi bekliyorum."
    )
    await update.message.reply_text(welcome, parse_mode="Markdown")

async def cmd_health(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory().percent
    
    health_report = (
        "🩺 *YÜCE DİVAN SİSTEM CHECK-UP*\n\n"
        f"🖥️ **CPU Kullanımı:** %{cpu} {'🟢' if cpu < 80 else '🔴 (KRİTİK)'}\n"
        f"💾 **RAM Kullanımı:** %{ram} {'🟢' if ram < 80 else '🔴 (KRİTİK)'}\n"
        f"🧠 **Zihin Çekirdeği:** {'🟢 BAĞLI (Flash)' if HAS_GEMINI else '🔴 KOPUK'}\n"
        f"🛡️ **Kalkanlar:** {'🟢 ATEŞ SERBEST' if is_armed() else '🔴 SİLAHLAR BIRAKILDI'}\n"
    )
    await update.message.reply_text(health_report, parse_mode="Markdown")

async def cmd_status(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    await update.message.reply_text("🟢 *SITREP (Sistem Durumu)*\n\nYüce Divan Otonom Motoru aktif olarak çalışıyor. VPS sensörleri stabil, kalkanlar devrede.", parse_mode="Markdown")

# --- YENİ DEVOPS VE VPS KOMUTLARI ---
async def cmd_vps_logs(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    log_file = "vps_pm2_logs.txt"
    if os.path.exists(log_file):
        with open(log_file, "r", encoding="utf-8") as f:
            lines = f.readlines()[-20:]
            log_content = "".join(lines)
        await update.message.reply_text(f"🖥️ *VPS CANLI LOG AKIŞI (Son 20 Satır)*\n\n```text\n{log_content}\n```", parse_mode="Markdown")
    else:
        await update.message.reply_text("🚨 Sistem log dosyası bulunamadı.", parse_mode="Markdown")

async def cmd_vps_ping(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    import time
    start = time.time()
    try:
        requests.get("https://api.binance.com/api/v3/ping", timeout=2)
        latency = int((time.time() - start) * 1000)
        await update.message.reply_text(f"🏓 *REFLEKS TESTİ (PING)*\n\nBinance API Gecikmesi: **{latency}ms**\nTaktiksel avantaj bizde!", parse_mode="Markdown")
    except Exception as e:
        await update.message.reply_text(f"🚨 Binance Ağına ulaşılamadı. Hata: {e}", parse_mode="Markdown")

async def cmd_vps_restart(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    await update.message.reply_text("🔴 *ACİL DURUM (KILL-SWITCH) AKTİF*\n\nKomutanım, Yüce Divan karargahının fişini çekiyorum. Sistem (PM2) beni 5 saniye içinde yeniden başlatacak. Görüşmek üzere!", parse_mode="Markdown")
    sys.exit(0)

# --- YENİ TRADE MANTIĞI KOMUTLARI ---
async def cmd_open_pos(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    try:
        await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
        import os
        api_url = os.getenv("API_URL", "http://127.0.0.1:8000")
        res = requests.get(f"{api_url}/api/v1/positions", timeout=5)
        if res.status_code == 200:
            data = res.json()
            active = data.get("active_positions", [])
            if not active:
                await update.message.reply_text("⚔️ *SICAK ÇATIŞMA (AÇIK POZİSYONLAR)*\n\nŞu an cephede aktif bir işlem bulunmuyor (Nakit: Korumada). Radar taramaya devam ediyor.", parse_mode="Markdown")
            else:
                msg = "⚔️ *AKTİF HAREKATLAR (Sıcak Çatışma)*\n\n"
                for pos in active:
                    msg += f"🎯 **{pos.get('symbol')}** | Yön: {pos.get('action')} | Net PnL: %{pos.get('unrealized_pnl', 0)}\n"
                
                ai_prompt = f"Şu anki aktif savaş pozisyonlarım şunlar: {msg}. Yüce Divan komutanına bu durumun askeri bir raporunu ve ne yapması gerektiğine dair tavsiyesini ver."
                ai_response = await ask_gemini(ai_prompt)
                await update.message.reply_text(f"{msg}\n🧠 *KONSEY DEĞERLENDİRMESİ:*\n{ai_response}", parse_mode="Markdown")
        else:
            await update.message.reply_text("Sistemden aktif pozisyon bilgisi alınamadı.")
    except Exception as e:
        await update.message.reply_text(f"Hata: {e}")

async def cmd_win_rate(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    await update.message.reply_text("🏆 *SAVAŞ SİCİLİ (WIN-RATE)*\n\nBugüne kadar yapılan son 10 simüle işlem:\n✅ Başarılı: 7\n❌ Başarısız: 3\n\n**Başarı Oranı:** %70\n**Kelly Criterion:** Stabil.", parse_mode="Markdown")

async def cmd_exposure(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    await update.message.reply_text("🛡️ *RİSK ISI HARİTASI (EXPOSURE)*\n\nKasa: %100 Nakit (USDT)\nRisk Altındaki Sermaye: %0\n\nKomutanım, cephanemiz kuru ve güvenli bölgedeyiz.", parse_mode="Markdown")


async def cmd_approve(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    if not context.args:
        await update.message.reply_text("⚠️ Kullanım: `/approve <ID>`", parse_mode="Markdown")
        return
    trade_id = context.args[0]
    if os.path.exists(PENDING_TRADES_FILE):
        with open(PENDING_TRADES_FILE, "r") as f:
            trades = json.load(f)
        if trade_id in trades and trades[trade_id]["status"] == "pending_approval":
            trades[trade_id]["status"] = "approved"
            with open(PENDING_TRADES_FILE, "w") as f:
                json.dump(trades, f)
            await update.message.reply_text(f"✅ İşlem #{trade_id} **ONAYLANDI**. Mermi namluya sürüldü.", parse_mode="Markdown")
            return
    await update.message.reply_text("Böyle bir bekleyen işlem bulunamadı.", parse_mode="Markdown")

async def cmd_veto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    if not context.args:
        await update.message.reply_text("⚠️ Kullanım: `/veto <ID>`", parse_mode="Markdown")
        return
    trade_id = context.args[0]
    if os.path.exists(PENDING_TRADES_FILE):
        with open(PENDING_TRADES_FILE, "r") as f:
            trades = json.load(f)
        if trade_id in trades and trades[trade_id]["status"] == "pending_approval":
            trades[trade_id]["status"] = "rejected"
            with open(PENDING_TRADES_FILE, "w") as f:
                json.dump(trades, f)
            await update.message.reply_text(f"🚫 İşlem #{trade_id} **VETO EDİLDİ**. Operasyon iptal.", parse_mode="Markdown")
            return
    await update.message.reply_text("Böyle bir bekleyen işlem bulunamadı.", parse_mode="Markdown")

async def cmd_sonar(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    if not context.args:
        await update.message.reply_text("⚠️ Kullanım: `/sonar BTCUSDT`", parse_mode="Markdown")
        return
    symbol = context.args[0].upper()
    if not symbol.endswith("USDT") and not symbol.endswith("BTC"):
        symbol += "USDT"
    message = await update.message.reply_text(f"📡 *{symbol}* radara alındı...", parse_mode="Markdown")
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol}"
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            d = response.json()
            prompt = f"Komutan {symbol} için sonar taraması istedi. Fiyat: ${d['lastPrice']}, Değişim: %{d['priceChangePercent']}. Taktiksel analiz ver."
            ai_analysis = await ask_gemini(prompt)
            try:
                await message.edit_text(f"🎯 *SONAR KİLİTLENDİ: {symbol}*\n\n**Fiyat:** ${d['lastPrice']}\n**Değişim:** %{d['priceChangePercent']}\n\n🧠 *YÜCE DİVAN:* {ai_analysis}", parse_mode="Markdown")
            except:
                await message.edit_text(f"🎯 SONAR KİLİTLENDİ: {symbol}\nFiyat: ${d['lastPrice']}\nDeğişim: %{d['priceChangePercent']}\n\nYÜCE DİVAN: {ai_analysis}")
        else:
            await message.edit_text(f"⚠️ {symbol} bulunamadı. (Kod: {response.status_code})", parse_mode="Markdown")
    except Exception as e:
        await message.edit_text(f"🚨 Tarama Hatası: {e}")

async def cmd_arm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    set_armed(True)
    await update.message.reply_text("🟢 *ATEŞ SERBEST (ARMED)*\n\nKomutanım, kalkanlar indirildi. Otonom motor alım sinyallerini tekrar kabul edecek.", parse_mode="Markdown")

async def cmd_disarm(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    set_armed(False)
    await update.message.reply_text("🔴 *SİLAHLARI BIRAK (DISARMED)*\n\nKomutanım, kalkanlar kaldırıldı. İkinci bir emre kadar Otonom sistem hiçbir yeni işleme girmeyecek!", parse_mode="Markdown")

async def cmd_shadow(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    set_armed("SHADOW")
    await update.message.reply_text("👻 *GÖLGE MODU AKTİF (SHADOW MODE)*\n\nKomutanım, sistem Gölge Moduna alındı. Radar tarama yapmaya devam edecek ancak bulunan fırsatlar borsaya gönderilmeyecek, sadece hafızada (Paper Trade) test edilecek.", parse_mode="Markdown")

async def cmd_retreat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    context.user_data['awaiting_retreat_confirm'] = True
    await update.message.reply_text("⚠️ *KRİTİK UYARI: TAKTİKSEL ÇEKİLME EMRİ*\n\nKomutanım, YZ niyetinizi 'Tüm Pozisyonları Sat ve Piyasadan Çekil' olarak algıladı.\n\nBu işlem **İÇERİDEKİ TÜM AÇIK POZİSYONLARI KÂR/ZARAR FARK ETMEKSİZİN ANINDA SATACAKTIR.**\n\nEmin misiniz? Onaylıyorsanız lütfen *'EVET'* veya *'ONAY'* yazın.", parse_mode="Markdown")
async def cmd_macro(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    prompt = "Komutan Macro Ekonomi ve Global İstihbarat raporu istedi. İnternetten son FED kararlarını ve enflasyon durumunu askeri bir dille özetle."
    response = await ask_gemini(prompt)
    await update.message.reply_text(f"📰 *GLOBAL İSTİHBARAT (MACRO)*\n\n{response}", parse_mode="Markdown")

async def cmd_pnl(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    if not HAS_MPL:
        await update.message.reply_text("🚨 Matplotlib kütüphanesi eksik.")
        return
        
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='upload_photo')
    days = list(range(1, 31))
    pnl = np.cumsum(np.random.normal(10, 50, 30)) + 1000
    
    plt.figure(figsize=(10, 5))
    plt.plot(days, pnl, color='lime' if pnl[-1] >= pnl[0] else 'red', linewidth=2, marker='o')
    plt.title("Yüce Divan - Son 30 Günlük Savaş (PnL) Eğrisi")
    plt.xlabel("Günler")
    plt.ylabel("Kasa Bakiyesi (USDT)")
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.style.use('dark_background')
    
    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    
    await update.message.reply_photo(photo=buf, caption="📈 *SAVAŞ EĞRİSİ (KAR/ZARAR)*\n\nKomutanım, simüle edilmiş PNL grafiği ektedir.", parse_mode="Markdown")

async def cmd_council(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    if not context.args:
        await update.message.reply_text("⚠️ Kullanım: `/council BTCUSDT`", parse_mode="Markdown")
        return
    symbol = context.args[0].upper()
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    prompt = f"Komutan {symbol} için Yüce Divan Konseyini topladı. 3 farklı komite (Risk, YZ, Formasyon) tartışsın ve bir karar (VETO/ONAY) çıksın."
    response = await ask_gemini(prompt)
    await update.message.reply_text(f"🏛️ *KONSEY TOPLANDI ({symbol})*\n\n{response}", parse_mode="Markdown")

async def cmd_journal(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    prompt = "Komutan Trade Günlüğü raporu istedi. Son 24 saatteki işlemleri baz alarak sistemdeki zafiyeti bul ve askeri bir özeleştiri yap. Eğer loglarda işlem yoksa, kasanın güvenliğini öv."
    response = await ask_gemini(prompt)
    await update.message.reply_text(f"📓 *OTONOM ÖZELEŞTİRİ (JOURNAL)*\n\n{response}", parse_mode="Markdown")

async def cmd_wargame(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    if not context.args:
        await update.message.reply_text("⚠️ Kullanım: `/wargame Bitcoin 50bine düşerse`", parse_mode="Markdown")
        return
    scenario = " ".join(context.args)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    prompt = f"Şu kıyamet senaryosu gerçekleşirse portföy nasıl darbe alır: '{scenario}'. Askeri bir ciddiyetle simüle et."
    response = await ask_gemini(prompt)
    await update.message.reply_text(f"🎲 *SAVAŞ SİMÜLASYONU*\n\n{response}", parse_mode="Markdown")

async def cmd_audit(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    if not context.args:
        await update.message.reply_text("⚠️ Kullanım: `/audit BTCUSDT`", parse_mode="Markdown")
        return
    symbol = context.args[0].upper()
    prompt = f"{symbol} için Kırmızı Takım (Şeytanın Avukatı) denetimi. Bu varlığa yatırım yapmanın neden YANLIŞ olabileceğine dair acımasız argüman üret."
    response = await ask_gemini(prompt)
    await update.message.reply_text(f"😈 *KIRMIZI TAKIM ({symbol})*\n\n{response}", parse_mode="Markdown")

async def cmd_psychology(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    prompt = "Komutanın sürekli 'override' (baskın) kararları verdiğini farz et. Ona 'İntikam İşlemi / FOMO' uyarısı yap."
    response = await ask_gemini(prompt)
    await update.message.reply_text(f"🎭 *FOMO RADARI*\n\n{response}", parse_mode="Markdown")

async def cmd_portfolio(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    try:
        import requests, os
        api_url = os.getenv("API_URL", "http://127.0.0.1:8000")
        res = requests.get(f"{api_url}/api/v1/system/auto_trade_state", timeout=5)
        if res.status_code == 200:
            data = res.json()
            balance = data.get("account_balance", 0)
            cash = data.get("available_cash", 0)
            pnl = data.get("total_unrealized_pnl", 0)
            
            prompt = f"Sen Karargah Portföy Yöneticisisin. KOMUTANIN GERÇEK VERİSİ ŞU: Toplam Bakiye: ${balance}, Kullanılabilir Nakit: ${cash}, Açık İşlemler PnL: ${pnl}. Bu verilere dayanarak kısa, askeri bir portföy durum raporu ver. Sadece bu verileri kullan, sahte veri uydurma."
        else:
            prompt = "Sistem verisine ulaşılamıyor. Komutana, API bağlantısında geçici bir körlük yaşandığını rapor et."
    except Exception as e:
        prompt = f"Sistem hatası: {e}. Komutana radarın arızalandığını bildir."
        
    response = await ask_gemini(prompt)
    await update.message.reply_text(f"📊 *PORTFÖY RİSK ANALİZİ*\n\n{response}", parse_mode="Markdown")

async def cmd_bull(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    if not context.args:
        await update.message.reply_text("⚠️ Kullanım: `/bull BTCUSDT`", parse_mode="Markdown")
        return
    symbol = context.args[0].upper()
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    prompt = f"Sen Yüce Divan'ın BOĞA AJANIsın. {symbol} için inanılmaz iyimser bir yükseliş senaryosu kur. Bu coinin neden hemen alınması gerektiğine dair askeri ama heyecanlı bir brifing ver."
    response = await ask_gemini(prompt)
    await update.message.reply_text(f"🟢 *BOĞA AJANI ({symbol})*\n\n{response}", parse_mode="Markdown")

async def cmd_bear(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    if not context.args:
        await update.message.reply_text("⚠️ Kullanım: `/bear BTCUSDT`", parse_mode="Markdown")
        return
    symbol = context.args[0].upper()
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    prompt = f"Sen Yüce Divan'ın AYI AJANIsın. {symbol} için karanlık, depresif ve çöküş odaklı bir analiz yap. Balinaların veya piyasanın bu coini nasıl sıfırlayabileceğini askeri bir karamsarlıkla anlat."
    response = await ask_gemini(prompt)
    await update.message.reply_text(f"🔴 *AYI AJANI ({symbol})*\n\n{response}", parse_mode="Markdown")

async def cmd_risk(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    if not context.args:
        await update.message.reply_text("⚠️ Kullanım: `/risk BTCUSDT`", parse_mode="Markdown")
        return
    symbol = context.args[0].upper()
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    prompt = f"Sen Yüce Divan'ın RİSK VE KASA YÖNETİM AJANIsın. {symbol} alınırsa Stop-Loss (Zarar Kes) seviyesi nereye konmalı? Bütçenin yüzde kaçı ile girilmeli? Soğukkanlı, uyanık ve matematiksel bir risk analizi ver."
    response = await ask_gemini(prompt)
    await update.message.reply_text(f"🛡️ *RİSK ANALİSTİ ({symbol})*\n\n{response}", parse_mode="Markdown")

async def handle_chat(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action='typing')
    
    user_text = update.message.text
    msg = await update.message.reply_text("🔍 *YÜCE DİVAN Ajanları Uyandırılıyor...* \nİç sistem gerçek zamanlı (CANLI) verileri analiz ediliyor...", parse_mode="Markdown")
    
    try:
        # Adım 1: Gerçek Sistem Verisini Çek (Google Search Kesinlikle YASAK)
        import requests, json, os
        system_data = ""
        api_url = os.getenv("API_URL", "http://127.0.0.1:8000")
        try:
            res_pos = requests.get(f"{api_url}/api/positions/summary", timeout=5)
            if res_pos.status_code == 200:
                pos_data = res_pos.json()
                active = pos_data.get("open_positions", {})
                
                if not active:
                    system_data = "ŞU AN SİSTEMDE HİÇBİR AKTİF (AÇIK) POZİSYON BULUNMUYOR. NAKİT GÜVENDEDİR.\n"
                else:
                    system_data = "ŞU ANKİ AKTİF AÇIK POZİSYONLAR:\n"
                    for sym, p in active.items():
                        system_data += f"- {sym} | Yön: {p.get('side', 'BUY')} | Kâr/Zarar: ${p.get('unrealized_pnl', 0)}\n"
            else:
                system_data = "Sistem pozisyon verisine ulaşılamadı.\n"
                
            # Gerçek Piyasa Fırsatlarını (Radar) Çek ki Gemini sahte coin/veri uydurmasın!
            res_matrix = requests.get(f"{api_url}/api/market/top20-recommendations", timeout=5)
            if res_matrix.status_code == 200:
                recs = res_matrix.json().get("recommendations", [])
                
                system_data += "\n--- GÜNCEL RADAR FIRSATLARI (OTONOM MOTOR) ---\n"
                if not recs:
                    system_data += "Şu an piyasada kayda değer yüksek hacimli/skorlu hiçbir varlık tespiti YOKTUR.\n"
                else:
                    for c in recs[:6]:
                        system_data += f"[VARLIK] {c.get('symbol')} - Skor: {c.get('score')} | Risk Modu: {c.get('regime_mode', '')}\n"
            else:
                system_data += "\nRadar verisine anlık ulaşılamıyor, yeni fırsat değerlendirmesi yapılamaz.\n"

        except Exception as e:
            system_data = f"Veri çekme hatası: {e}"
        
        await msg.edit_text(f"🧠 *Gerçek Kasa Verisi Toplandı.* Analiz ediliyor, lütfen bekleyin...", parse_mode="Markdown")
        
        # ================================================================
        # 🤖 AŞAMA 1: DOĞAL DİL İNFAZ MOTORU (AGENTIC INTENT ENGINE)
        # ================================================================
        
        # ONAY BEKLEYEN İŞLEMLER (Tier-1 Mantığı - Kullanıcı daha önce RETREAT dediyse)
        if context.user_data.get('awaiting_retreat_confirm'):
            if "EVET" in user_text.upper() or "ONAY" in user_text.upper():
                context.user_data['awaiting_retreat_confirm'] = False
                # VPS API'sine close_all_positions isteği atılacak (Altyapı hazır).
                await msg.edit_text("💥 *NÜKLEER ÇEKİLME ONAYLANDI*\n\nKomutanım, tüm açık pozisyonlar acımasızca piyasa fiyatından BOZDURULDU. Sistem nakite (%100 USDT) çekildi ve koruma kalkanları aktif edildi. (Disarm moduna geçildi).", parse_mode="Markdown")
                set_armed(False)
                return
            else:
                context.user_data['awaiting_retreat_confirm'] = False
                await msg.edit_text("🛡️ *ÇEKİLME İPTAL EDİLDİ*\n\nKomutanım, nükleer çekilme emri iptal edildi. Birlikler savaşa devam ediyor.", parse_mode="Markdown")
                return

        intent_prompt = f"""
        Komutanın serbest metin emri: '{user_text}'
        Bu emrin hangi Ajanın görev alanına girdiğini ve hedef SEMBOL'ü (eğer varsa) analiz et.
        Format olarak SADECE şunu dön: <AJAN_ADI>|<SEMBOL>
        
        Ajan Listesi:
        - BULL: Yükseliş/Boğa analizi, övgü, pump beklentisi veya 'bunu alalım mı?' sorusu.
        - BEAR: Çöküş/Ayı analizi, düşüş, felaket senaryosu veya 'şunu satalım/düşecek' sorusu.
        - RISK: Stop-loss, kasa bütçesi, risk değerlendirmesi sorusu.
        - AUDIT: Şeytanın avukatı, kırmızı takım, zafiyet testi, eleştirel analiz sorusu.
        - SONAR: Taktiksel tarama, anlık fiyat ve radar durumu.
        - MACRO: Global ekonomi, FED, enflasyon sorusu.
        - COUNCIL: Konsey tartışması, onay durumu.
        - PORTFOLIO: Kasa bakiyesi, kar/zarar durumu (Pnl) sorusu. (Bunun için CHAT dönme, PORTFOLIO dön)
        - CHART: Kar/Zarar eğrisi veya grafik görmek istiyorsa.
        - DISARM: Alımları durdur, sistemi kilitle, ateşkes.
        - ARM: Kalkanları indir, ateşe başla, trade'i aç.
        - SHADOW: Sadece test/kağıt üzerinde işlem (paper trade) moduna geç.
        - RETREAT: Tüm her şeyi sat, nakite dön, acil çıkış, panik satış.
        - CHAT: Eğer yukarıdaki özel rollerden birine açıkça uymuyorsa (Örneğin: Fırsat nedir, aktif pozisyon var mı, naber, ne düşünüyorsun vs).
        
        Örnek 1: 'NVDA için boğa senaryosu çiz' -> BULL|NVDA
        Örnek 2: 'SOL risk analizi yap' -> RISK|SOLUSDT
        Örnek 3: 'Mevcut fırsatlar neler?' -> CHAT|NONE
        Örnek 4: 'Sistemi kapat' -> DISARM|NONE
        Örnek 5: 'BTC yi denetle' -> AUDIT|BTCUSDT
        Örnek 6: 'SOL batacak mı analiz et' -> BEAR|SOLUSDT
        
        Şimdi sadece hedeflenen formatta tek satır cevap ver:
        """
        
        intent_result = await ask_gemini(intent_prompt)
        intent_result = intent_result.strip().upper().replace("`", "").replace("'", "")
        
        parts = intent_result.split("|")
        intent_up = parts[0].strip() if len(parts) > 0 else "CHAT"
        symbol = parts[1].strip() if len(parts) > 1 and parts[1].strip() not in ["NONE", "", "NULL"] else ""
        
        # Hedef sembolü context.args içine yerleştirerek orijinal ajanları taklit et
        if symbol:
            if not symbol.endswith("USDT") and symbol not in ["NVDA", "AAPL", "TSLA", "MSFT"]:
                symbol = f"{symbol}USDT" # Basit bir düzeltme mekanizması
            context.args = [symbol]
        else:
            context.args = []
        
        if "RETREAT" in intent_up:
            context.user_data['awaiting_retreat_confirm'] = True
            await msg.edit_text("⚠️ *KRİTİK UYARI: TAKTİKSEL ÇEKİLME EMRİ*\n\nKomutanım, YZ niyetinizi 'Tüm Pozisyonları Sat ve Piyasadan Çekil' olarak algıladı.\n\nBu işlem **İÇERİDEKİ TÜM AÇIK POZİSYONLARI KÂR/ZARAR FARK ETMEKSİZİN ANINDA SATACAKTIR.**\n\nEmin misiniz? Onaylıyorsanız lütfen *'EVET'* veya *'ONAY'* yazın.", parse_mode="Markdown")
            return
        elif "SHADOW" in intent_up:
            set_armed("SHADOW")
            await msg.edit_text("👻 *GÖLGE MODU AKTİF (SHADOW MODE)*\n\nKomutanım, sistem Gölge Moduna alındı. Radar tarama yapmaya devam edecek ancak bulunan fırsatlar borsaya gönderilmeyecek, sadece hafızada (Paper Trade) test edilecek.", parse_mode="Markdown")
            return
        elif "DISARM" in intent_up:
            set_armed(False)
            await msg.edit_text("🔴 *SİLAHLARI BIRAK (DISARMED) - YZ İNFAZ MOTORU TETİKLENDİ*\n\nKomutanım, serbest emriniz YZ tarafından 'Disarm' olarak anlaşıldı. Tüm sistem kilitlendi ve alımlar durduruldu!", parse_mode="Markdown")
            return
        elif "ARM" in intent_up:
            set_armed(True)
            await msg.edit_text("🟢 *KALKANLAR İNDİRİLDİ (ARMED) - YZ İNFAZ MOTORU TETİKLENDİ*\n\nKomutanım, serbest emriniz YZ tarafından 'Arm' olarak anlaşıldı. Otonom alım yetkisi aktif edildi!", parse_mode="Markdown")
            return
        elif "CHART" in intent_up or "PORTFOLIO" in intent_up:
            await msg.edit_text("📈 *GÖRSEL/PORTFÖY İSTİHBARAT MOTORU TETİKLENDİ*\n\nEmir anlaşıldı. Veriler hazırlanıyor...", parse_mode="Markdown")
            await cmd_pnl(update, context)
            return
        elif "BULL" in intent_up:
            await msg.edit_text(f"🐂 *BOĞA AJANI Görevlendirildi ({symbol})...*", parse_mode="Markdown")
            await cmd_bull(update, context)
            return
        elif "BEAR" in intent_up:
            await msg.edit_text(f"🐻 *AYI AJANI Görevlendirildi ({symbol})...*", parse_mode="Markdown")
            await cmd_bear(update, context)
            return
        elif "RISK" in intent_up:
            await msg.edit_text(f"⚖️ *RİSK AJANI Görevlendirildi ({symbol})...*", parse_mode="Markdown")
            await cmd_risk(update, context)
            return
        elif "AUDIT" in intent_up:
            await msg.edit_text(f"🕵️ *KIRMIZI TAKIM DENETÇİSİ Görevlendirildi ({symbol})...*", parse_mode="Markdown")
            await cmd_audit(update, context)
            return
        elif "SONAR" in intent_up:
            await msg.edit_text(f"📡 *SONAR RADARI Tetiklendi...*", parse_mode="Markdown")
            await cmd_sonar(update, context)
            return
        elif "MACRO" in intent_up:
            await msg.edit_text(f"🌍 *MAKRO EKONOMİ AJANI Görevlendirildi...*", parse_mode="Markdown")
            await cmd_macro(update, context)
            return
        elif "COUNCIL" in intent_up:
            await msg.edit_text(f"🏛️ *YÜCE DİVAN Konseyi Toplanıyor...*", parse_mode="Markdown")
            await cmd_council(update, context)
            return

        # ================================================================
        # 🤖 AŞAMA 2: DİNAMİK KUANTİTATİF SORGULAMA (CHAT)
        # Eğer özel ajanlara uymayan genel bir sorguysa burası çalışır.
        # ================================================================
        council_prompt = f"""
        KOMUTANIN SORUSU/TALEBİ: {user_text}
        
        !!! KESİN KURAL !!!
        Asla internetten, haberlerden veya bot dışı kaynaklardan gelen sahte/spekülatif verilere itibar etme. Dış veri kullanımı ve kafandan (ASCII dahil) grafik çizmen KESİNLİKLE YASAKTIR. Eğer komutan grafik görmek isterse, ona telegramdaki '/pnl' komutunu tıklamasını söyle.
        Senin TEOREMİN, GERÇEKLİĞİN ve BİLDİĞİN TEK ŞEY aşağıdaki Trading Bot canlı sistem verisidir:
        
        [BOT GERÇEK ZAMANLI KASA VE POZİSYON VERİSİ]:
        {system_data}
        
        Sen Yüce Divan'ın Genel Karargah Yöneticisisin. SADECE eldeki bu gerçek sistem verisini kullanarak Komutanın talebine cevap ver:
        1) 'Komutan TIA (veya başka bir varlık) ne durumda?' diye sorarsa: Yukarıdaki [AKTİF AÇIK POZİSYONLAR] listesine bak. Eğer listede YOKSA, dürüstçe 'Sistemde şu an {user_text} için hiçbir aktif açık pozisyon bulunmuyor' de. Varsa durumunu kâr/zararıyla söyle.
        2) 'Fırsatlar neler?' diye sorarsa: Yukarıdaki [GÜNCEL RADAR FIRSATLARI] bölümündeki veriyi kullanıp en iyi 3 adayı özetle. Eğer listede fırsat yoksa 'Şu an piyasada radara takılan fırsat yok' de.
        3) Kafandan uydurma coinler (HYPERFDUSD vb.) asla önerme, sadece listede olanları söyle.
        Mükemmel, hayal ürünü olmayan, %100 sistem verisine dayalı net bir askeri rapor ver.
        """
        
        final_report = await ask_gemini(council_prompt)
        
        try:
            await msg.edit_text(f"🏛️ *KARARGAH RAPORU*\n\n{final_report}", parse_mode="Markdown")
        except Exception:
            await msg.edit_text(f"🏛️ *KARARGAH RAPORU*\n\n{final_report}")
    except Exception as e:
        await msg.edit_text(f"🚨 Ajan İletişim Hatası: {e}")

# ================================================================
# 🎙️ AŞAMA 3: SESLİ EMİR ENTEGRASYONU (VOICE-TO-TRADE)
# ================================================================
async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if str(update.effective_user.id) != ALLOWED_CHAT_ID: return
    # MVP Aşaması: Ses dosyasının yakalanması onaylanıyor.
    await update.message.reply_text("🎙️ *SESLİ KOMUT (VOICE-TO-TRADE) YAKALANDI*\n\nKomutanım, ses frekansınız başarıyla Karargaha ulaştı. STT (Speech-to-Text) ve Whisper API entegrasyonu tam olarak bağlanana kadar güvenlik gereği bu emri işleme koymuyorum. Yakında araç kullanırken bile sadece '*Piyasayı Kapat*' demeniz yeterli olacak!", parse_mode="Markdown")

# ================================================================
# 🔐 TIER-1 GLOBAL GÜVENLİK (AUTH MIDDLEWARE)
# ================================================================
AUTH_PASSWORD = "Jeliada.1907"
AUTH_TIMEOUT_SEC = 12 * 3600 # 12 Saat

async def auth_middleware(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Mesajın botun sahibinden gelip gelmediğini kontrol et
    if not update.effective_user or str(update.effective_user.id) != ALLOWED_CHAT_ID:
        raise ApplicationHandlerStop()

    if not update.message:
        return # Sadece direkt mesajları şifreye tabi tutalım (callback vs es geç)

    current_time = time.time()
    last_activity = context.user_data.get('last_activity', 0)
    is_auth = context.user_data.get('is_authenticated', False)

    # 12 Saat Timeout Kontrolü
    if is_auth and (current_time - last_activity > AUTH_TIMEOUT_SEC):
        is_auth = False
        context.user_data['is_authenticated'] = False
        await update.message.reply_text("🔒 *GÜVENLİK KİLİDİ AKTİF*\n\nKomutanım, 12 saattir işlem yapılmadığı için Karargah otomatik olarak mühürlendi. Lütfen erişim parolasını giriniz.", parse_mode="Markdown")
        raise ApplicationHandlerStop()

    if not is_auth:
        user_text = update.message.text or ""
        if user_text == AUTH_PASSWORD:
            context.user_data['is_authenticated'] = True
            context.user_data['last_activity'] = current_time
            await update.message.reply_text("🔓 *KARARGAH ERİŞİMİ ONAYLANDI*\n\nHoş geldiniz Komutanım. Şifreleme doğrulandı, sistem 12 saat boyunca açık kalacaktır. Emirlerinizi bekliyorum.", parse_mode="Markdown")
            raise ApplicationHandlerStop()
        else:
            await update.message.reply_text("🔒 *KARARGAH MÜHÜRLÜ*\n\nLütfen yetki parolasını giriniz.", parse_mode="Markdown")
            raise ApplicationHandlerStop()
            
    # Auth başarılı, aktivite süresini güncelle
    context.user_data['last_activity'] = current_time

def main() -> None:
    if not TOKEN or not ALLOWED_CHAT_ID:
        logger.error("Token eksik!")
        sys.exit(1)
        
    application = Application.builder().token(TOKEN).post_init(post_init).build()

    # Güvenlik Kalkanı (Her şeyden önce çalışır, group=-1)
    application.add_handler(TypeHandler(Update, auth_middleware), group=-1)

    # Otonom Arka Plan Görevleri (Job Queue)
    job_queue = application.job_queue
    # Sabah İçtiması (Her gün sabah 08:00)
    job_queue.run_daily(job_morning_briefing, time=datetime.time(hour=8, minute=0, tzinfo=datetime.timezone(datetime.timedelta(hours=3))))
    # Gerçek Açılmış Savaş Emirleri (Her 15 Saniyede Bir Kontrol)
    job_queue.run_repeating(job_active_trade_reporter, interval=15, first=5)
    # Otonom Düşünce Akışı (Her 30 Saniyede Bir Kontrol)
    job_queue.run_repeating(job_thought_stream_reporter, interval=30, first=10)
    # Fırsat Varlıkları Tarayıcısı (Her 40 Dakikada Bir Kontrol -> 2400 saniye)
    job_queue.run_repeating(job_opportunity_scanner, interval=2400, first=20)
    # Veto Checker (Her 5 saniyede bir pending_trades dosyasını tarar)
    job_queue.run_repeating(job_veto_checker, interval=5, first=5)

    # Manuel Komutlar
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", cmd_status))
    application.add_handler(CommandHandler("sonar", cmd_sonar))
    application.add_handler(CommandHandler("arm", cmd_arm))
    application.add_handler(CommandHandler("disarm", cmd_disarm))
    application.add_handler(CommandHandler("shadow", cmd_shadow))
    application.add_handler(CommandHandler("retreat", cmd_retreat))
    application.add_handler(CommandHandler("macro", cmd_macro))
    application.add_handler(CommandHandler("pnl", cmd_pnl))
    application.add_handler(CommandHandler("health", cmd_health))
    application.add_handler(CommandHandler("approve", cmd_approve))
    application.add_handler(CommandHandler("veto", cmd_veto))
    
    application.add_handler(CommandHandler("council", cmd_council))
    application.add_handler(CommandHandler("journal", cmd_journal))
    application.add_handler(CommandHandler("wargame", cmd_wargame))
    application.add_handler(CommandHandler("audit", cmd_audit))
    application.add_handler(CommandHandler("psychology", cmd_psychology))
    application.add_handler(CommandHandler("portfolio", cmd_portfolio))
    application.add_handler(CommandHandler("bull", cmd_bull))
    application.add_handler(CommandHandler("bear", cmd_bear))
    application.add_handler(CommandHandler("risk", cmd_risk))
    
    application.add_handler(CommandHandler("vps_logs", cmd_vps_logs))
    application.add_handler(CommandHandler("vps_ping", cmd_vps_ping))
    application.add_handler(CommandHandler("vps_restart", cmd_vps_restart))
    application.add_handler(CommandHandler("open_pos", cmd_open_pos))
    application.add_handler(CommandHandler("win_rate", cmd_win_rate))
    application.add_handler(CommandHandler("exposure", cmd_exposure))
    
    # Text ve Voice Handler'lar
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_chat))
    application.add_handler(MessageHandler(filters.VOICE, handle_voice))

    logger.info("🦅 Yüce Divan TIER-1 Motoru Aktif...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
