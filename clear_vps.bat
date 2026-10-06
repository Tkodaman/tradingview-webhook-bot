gcloud compute scp scratch\clear_db.py instance-20261003-182635:/home/ASUS/tradingview-webhook-bot/scratch/clear_db.py --zone=europe-west4-a --project=tolgakodaman
gcloud compute ssh instance-20261003-182635 --zone=europe-west4-a --project=tolgakodaman --command="cd /home/ASUS/tradingview-webhook-bot; source venv/bin/activate; python scratch/clear_db.py"
