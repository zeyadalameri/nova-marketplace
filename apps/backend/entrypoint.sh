#!/bin/sh
set -eu

python manage.py migrate --noinput
python manage.py collectstatic --noinput
if [ "$#" -gt 0 ]; then
    exec "$@"
fi
exec uvicorn nova_api.asgi:application --host 0.0.0.0 --port 8000 --workers "${WEB_CONCURRENCY:-2}" --proxy-headers
