@echo off
gcloud compute ssh instance-20261003-182635 --zone=europe-west4-a --project=tolgakodaman --command="grep 'BTCUSDT' /home/ASUS/tradingview-webhook-bot/logs/bot.log | tail -n 20" > vps_btc_logs.txt
