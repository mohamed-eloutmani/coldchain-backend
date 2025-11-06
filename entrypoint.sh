#!/usr/bin/env bash
set -e

# Wait for Postgres
python - <<'PY'
import os, time, psycopg
from psycopg.rows import dict_row

host=os.getenv("POSTGRES_HOST","db"); port=os.getenv("POSTGRES_PORT","5432")
user=os.getenv("POSTGRES_USER","coldchain"); pwd=os.getenv("POSTGRES_PASSWORD","coldchain")
db=os.getenv("POSTGRES_DB","coldchain")

for i in range(30):
    try:
        with psycopg.connect(f"dbname={db} user={user} password={pwd} host={host} port={port}", connect_timeout=3) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SELECT 1;")
                print("[entrypoint] DB OK")
                raise SystemExit(0)
    except Exception as e:
        print(f"[entrypoint] waiting DB... ({i+1}/30): {e}")
        time.sleep(1)
raise SystemExit(1)
PY

# Migrate & run
python manage.py migrate --noinput
python manage.py runserver 0.0.0.0:8000
