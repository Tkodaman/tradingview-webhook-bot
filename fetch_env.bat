@echo off
gcloud compute ssh instance-20261003-182635 --zone=europe-west4-a --project=tolgakodaman --command="cat /home/ASUS/tradingview-webhook-bot/.env | grep TRADING_MODE" > vps_env.txt
