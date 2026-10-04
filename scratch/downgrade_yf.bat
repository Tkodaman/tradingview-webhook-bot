gcloud compute ssh instance-20261003-182635 --zone=europe-west4-a --project=tolgakodaman --command="pip3 install yfinance==0.2.40 --break-system-packages && pm2 restart tv-bot"
