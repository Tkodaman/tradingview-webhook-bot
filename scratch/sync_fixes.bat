gcloud compute scp services/engine/auto_runner.py instance-20261003-182635:~/tradingview-webhook-bot/services/engine/auto_runner.py --zone=europe-west4-a --project=tolgakodaman
gcloud compute scp core/security.py instance-20261003-182635:~/tradingview-webhook-bot/core/security.py --zone=europe-west4-a --project=tolgakodaman
gcloud compute ssh instance-20261003-182635 --zone=europe-west4-a --project=tolgakodaman --command="sed -i 's/^ALLOWED_IPS=.*/ALLOWED_IPS=*/g' ~/tradingview-webhook-bot/.env && pm2 restart tv-bot"
