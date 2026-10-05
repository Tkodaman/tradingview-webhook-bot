import psutil
import sys

def restart_bot():
    print("Finding python processes...")
    killed_any = False
    for p in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if p.info['name'] and 'python' in p.info['name'].lower():
                cmd = p.info.get('cmdline') or []
                cmd_str = ' '.join(cmd)
                # Kendi scriptimizi (restart_bot.py) ve system processleri haric tutalim
                if 'restart_bot.py' in cmd_str or 'antigravity' in cmd_str.lower() or 'psutil' in cmd_str:
                    continue
                
                # uvicorn main:app veya python main.py ise
                if 'uvicorn' in cmd_str or 'main.py' in cmd_str or 'tv-bot' in cmd_str or 'main:app' in cmd_str:
                    print(f"Killed process {p.info['pid']} - {cmd_str}")
                    p.kill()
                    killed_any = True
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass
            
    if not killed_any:
        print("Bot sureci bulunamadi.")
    else:
        print("Bot basariyla durduruldu.")

if __name__ == '__main__':
    restart_bot()
