gcloud compute ssh instance-20261003-182635 --zone=europe-west4-a --project=tolgakodaman --command="pip3 install websockets==16.1.1 yfinance==1.7.0 --break-system-packages && pm2 restart tv-bot"
