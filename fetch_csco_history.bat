@echo off
gcloud compute ssh instance-20261003-182635 --zone=europe-west4-a --project=tolgakodaman --command="sqlite3 /home/ASUS/tradingview-webhook-bot/bot_database.db \"SELECT * FROM trade_history WHERE symbol='CSCO' ORDER BY id DESC LIMIT 5;\"" > vps_csco_history.txt
