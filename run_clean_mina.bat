@echo off
echo ===================================================
echo VPS Uzerinde MINAUSDT Temizligi Baslatiliyor...
echo ===================================================
call gcloud compute ssh instance-20261003-182635 --zone=europe-west4-a --project=tolgakodaman --tunnel-through-iap --command="cd /home/ASUS/tradingview-webhook-bot && source .venv/bin/activate && python clean_mina.py && pm2 restart tv-bot"
echo Temizlik ve Restart Tamamlandi!
