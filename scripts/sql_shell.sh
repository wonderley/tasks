#!/usr/bin/env bash
# Launch an interactive psql session against the local Postgres database
# defined in docker-compose.yml.
#
# Usage (from repository root):
#   ./scripts/sql_shell.sh                  # connect with defaults
#   DB_NAME=mydb DB_USER=alice ./scripts/sql_shell.sh
#
# Environment variables (all optional):
#   DB_SERVICE   – docker-compose service name (default: db)
#   DB_USER      – Postgres role to connect as       (default: user)
#   DB_NAME      – database name to connect to       (default: taskdb)
#
# The script uses `docker compose exec` so you don't need the `psql` CLI
# installed on your host machine. It will start the database container if
# it is not already running.
set -euo pipefail

# Ensure we are executed from repository root so docker-compose.yml is visible.
if [ ! -f "docker-compose.yml" ]; then
  echo "Error: please run this script from the project root (./scripts/sql_shell.sh)" >&2
  exit 1
fi

SERVICE_NAME="${DB_SERVICE:-db}"
DB_USER="${DB_USER:-user}"
DB_NAME="${DB_NAME:-taskdb}"

# Start the DB container if it is not up yet
printf "\033[1m🔄 Ensuring Docker container '%s' is running…\033[0m\n" "$SERVICE_NAME"
docker compose up -d "$SERVICE_NAME"

printf "\033[1m🐘 Opening psql session to database '%s' as user '%s'…\033[0m\n" "$DB_NAME" "$DB_USER"
# The -u for user belongs to psql; we rely on the DB "user" having access.
# Pass -it for interactive TTY so arrow keys / readline work.
docker compose exec -it "$SERVICE_NAME" psql -U "$DB_USER" -d "$DB_NAME" 