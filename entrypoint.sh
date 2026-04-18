#!/bin/bash
set -e

if [ -z "$DATABASE_URL" ]; then
    echo "Error: DATABASE_URL is not set"
    exit 1
fi

echo "Waiting for PostgreSQL..."
python << END
import sys
import time
import psycopg

for i in range(30):
    try:
        psycopg.connect(conninfo="${DATABASE_URL}")
        print("PostgreSQL is ready!")
        break
    except psycopg.OperationalError:
        print(f"PostgreSQL not ready, retrying ({i+1}/30)...")
        time.sleep(1)
else:
    print("Could not connect to PostgreSQL")
    sys.exit(1)
END

echo "Running migrations..."
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput

exec "$@"
