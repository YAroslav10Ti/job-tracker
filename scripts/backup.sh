#!/usr/bin/env bash
# Бэкап PostgreSQL: кладёт дамп в backups/ и удаляет дампы старше 14 дней.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p backups
docker compose exec -T db pg_dump -U postgres job_tracker | gzip > "backups/job_tracker_$(date +%F_%H%M).sql.gz"
find backups -name '*.sql.gz' -mtime +14 -delete
