sudo apt-get update
sudo apt-get install -y postgresql postgresql-contrib
sudo -u postgres psql -c "CREATE DATABASE trading_bot;"
sudo -u postgres psql -c "CREATE USER bot_user WITH PASSWORD 'BotStrongPass123!';"
sudo -u postgres psql -c "ALTER ROLE bot_user SET client_encoding TO 'utf8';"
sudo -u postgres psql -c "ALTER ROLE bot_user SET default_transaction_isolation TO 'read committed';"
sudo -u postgres psql -c "ALTER ROLE bot_user SET timezone TO 'UTC';"
sudo -u postgres psql -c "GRANT ALL PRIVILEGES ON DATABASE trading_bot TO bot_user;"
sudo -u postgres psql -c "ALTER DATABASE trading_bot OWNER TO bot_user;"

PG_CONF=$(sudo find /etc/postgresql/ -name postgresql.conf)
sudo sed -i "s/#listen_addresses = 'localhost'/listen_addresses = '*'/g" $PG_CONF

HBA_CONF=$(sudo find /etc/postgresql/ -name pg_hba.conf)
echo "host    all             all             0.0.0.0/0               scram-sha-256" | sudo tee -a $HBA_CONF

sudo systemctl restart postgresql
