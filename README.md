

## Start docker container
docker compose up -d

## Access the DB
psql -h localhost -p 5433 -U user -d taskdb

## Run server
./scripts/run_local.sh