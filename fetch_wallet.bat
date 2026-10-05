@echo off
gcloud compute ssh instance-20261003-182635 --zone=europe-west4-a --project=tolgakodaman --command="cat /home/ASUS/tradingview-webhook-bot/db/wallet_state.json" > vps_wallet.json
