#!/usr/bin/env bash
# Backup script conforme ISO 27001 per PostgreSQL
# Usage: ./backup_postgres.sh <dest_dir>
# Richiede variabili env: PGHOST, PGPORT, PGUSER, PGPASSWORD, PGDATABASE
set -euo pipefail

DEST_DIR=${1:-"./backups"}
TIMESTAMP=$(date +"%Y%m%dT%H%M%S")
mkdir -p "$DEST_DIR"

OUTPUT="$DEST_DIR/pg_backup_${PGDATABASE:-db}_${TIMESTAMP}.sql.gz"
pg_dump -Fp --no-owner --no-privileges "$PGDATABASE" | gzip > "$OUTPUT"

# Verifica integrità del file generato
if gzip -t "$OUTPUT"; then
  echo "Backup completato: $OUTPUT"
else
  echo "Backup fallito" >&2
  exit 1
fi
