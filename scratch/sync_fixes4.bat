call gcloud compute scp core/security.py instance-20261003-182635:/home/ASUS/tradingview-webhook-bot/core/security.py --zone=europe-west4-a --project=tolgakodaman
call gcloud compute ssh instance-20261003-182635 --zone=europe-west4-a --project=tolgakodaman --command="pm2 restart tv-bot"
