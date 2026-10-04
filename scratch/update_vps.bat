gcloud compute ssh instance-20261003-182635 --zone=europe-west4-a --project=tolgakodaman --command="cd ~/tradingview-webhook-bot && git stash && git pull origin master && pm2 restart tv-bot"
