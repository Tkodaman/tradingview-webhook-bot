@echo off
echo ===================================================
echo [1/4] KODLAR PAKETLENIYOR (Gereksiz dosyalar haric)...
echo ===================================================
tar -cf deploy.tar --exclude=".venv" --exclude="__pycache__" --exclude=".git" --exclude="*.log" --exclude="*.db" --exclude="scratch" *

echo ===================================================
echo [2/4] PAKET VPS'E (GOOGLE CLOUD) GONDERILIYOR...
echo ===================================================
call gcloud compute scp deploy.tar instance-20261003-182635:/home/ASUS/deploy.tar --zone=europe-west4-a --project=tolgakodaman

echo ===================================================
echo [3/4] VPS UZERINDE DOSYALAR ACILIYOR VE BOT YENIDEN BASLATILIYOR...
echo ===================================================
call gcloud compute ssh instance-20261003-182635 --zone=europe-west4-a --project=tolgakodaman --command="tar -xf /home/ASUS/deploy.tar -C /home/ASUS/tradingview-webhook-bot && rm /home/ASUS/deploy.tar && pm2 restart tv-bot --update-env && pm2 ls"

echo ===================================================
echo [4/4] TEMIZLIK YAPILIYOR...
echo ===================================================
del deploy.tar

echo.
echo ===================================================
echo BASARILI! YENI KODLAR CANLIYA ALINDI VE BOT KESINTISIZ DEVAM EDIYOR.
echo ===================================================
