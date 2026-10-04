gcloud compute scp scratch\setup_pg.sh instance-20261003-182635:~/setup_pg.sh --zone=europe-west4-a --project=tolgakodaman
gcloud compute ssh instance-20261003-182635 --zone=europe-west4-a --project=tolgakodaman --command="bash ~/setup_pg.sh"
