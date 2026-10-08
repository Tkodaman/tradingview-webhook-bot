@echo off
call gcloud compute ssh instance-20261003-182635 --zone=europe-west4-a --project=tolgakodaman --tunnel-through-iap --command="pm2 restart konsey-raporu"
echo Rapor Tetiklendi!
