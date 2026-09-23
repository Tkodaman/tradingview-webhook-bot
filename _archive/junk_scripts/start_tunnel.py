"""
TradingView Canlı Webhook Tünel Başlatıcı (IPv4 127.0.0.1 Garantili)
"""

import subprocess
import sys
import time

def start_tunnel():
    print("=" * 68)
    print("  TRADINGVIEW CANLI WEBHOOK TÜNELİ BAŞLATILIYOR...")
    print("=" * 68)
    print("\n[BİLGİ] Port 8000 (127.0.0.1) tüneli internete açılıyor...")
    print(" Bağlantı kuruluyor, lütfen bekleyin...\n")

    # 127.0.0.1 IPv4 açıkça belirtilir (Windows IPv6 / localhost çakışmasını önler)
    cmd = [
        "ssh",
        "-o", "StrictHostKeyChecking=no",
        "-o", "UserKnownHostsFile=NUL",
        "-R", "80:127.0.0.1:8000",
        "nokey@localhost.run"
    ]

    try:
        proc = subprocess.Popen(cmd)
        proc.wait()
    except KeyboardInterrupt:
        print("\n[BİLGİ] Tünel kapatıldı.")
        try:
            proc.terminate()
        except:
            pass

if __name__ == "__main__":
    start_tunnel()
