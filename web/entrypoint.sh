#!/bin/sh
set -e

echo "=== [BIMLab Startup] Dang cho PostgreSQL 16 khoi dong... ==="
while ! python -c "
import psycopg2, os
try:
    conn = psycopg2.connect(
        dbname=os.environ.get('POSTGRES_DB', 'bimlab_db'),
        user=os.environ.get('POSTGRES_USER', 'bimlab_user'),
        password=os.environ.get('POSTGRES_PASSWORD', 'bimlab_secure_password_2026'),
        host=os.environ.get('POSTGRES_HOST', 'db'),
        port=os.environ.get('POSTGRES_PORT', '5432')
    )
    conn.close()
    exit(0)
except Exception:
    exit(1)
" 2>/dev/null; do
    sleep 1
done
echo "=== [BIMLab Startup] PostgreSQL 16 san sang! ==="

echo "=== [BIMLab Startup] Dang cho SeaweedFS Filer khoi dong... ==="
while ! python -c "
import urllib.request, os
try:
    url = os.environ.get('SEAWEEDFS_FILER_ENDPOINT', 'http://seaweedfs:8888') + '/'
    req = urllib.request.Request(url, method='HEAD')
    with urllib.request.urlopen(req, timeout=2) as resp:
        exit(0)
except Exception:
    exit(1)
" 2>/dev/null; do
    sleep 1
done
echo "=== [BIMLab Startup] SeaweedFS san sang! ==="

echo "=== [BIMLab Startup] Collect Static Files... ==="
python manage.py collectstatic --noinput

echo "=== [BIMLab Startup] Chay Migrations cho docs... ==="
python manage.py makemigrations docs --noinput
python manage.py migrate --noinput

echo "=== [BIMLab Startup] Khoi tao Storage & Du lieu Mau (v3)... ==="
python manage.py seed_workflows

echo "=== [BIMLab Startup] He thong san sang! Khoi chay Web Server... ==="
exec "$@"
