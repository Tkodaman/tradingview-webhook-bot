@echo off
gcloud compute ssh instance-20261003-182635 --zone=europe-west4-a --project=tolgakodaman --command="pm2 logs tv-bot --nostream --lines 50" > vps_pm2_logs.txt
