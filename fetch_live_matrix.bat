@echo off
call gcloud compute ssh instance-20261003-182635 --zone=europe-west4-a --project=tolgakodaman --tunnel-through-iap --command="curl -s http://localhost:8000/api/market/live-matrix > /tmp/live_matrix.json"
call gcloud compute scp instance-20261003-182635:/tmp/live_matrix.json .\scratch\live_matrix.json --zone=europe-west4-a --project=tolgakodaman --tunnel-through-iap
echo TAMAMLANDI
