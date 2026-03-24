#!/bin/sh
set -e

COMMAND="${1:-web}"

run_migrations() {
    echo "Running migrations..."
    uv run python manage.py migrate --noinput
}

case "$COMMAND" in
    web)
        # run_migrations
        echo "Starting Django development server..."
        exec uv run python manage.py runserver 0.0.0.0:8000
        ;;
    worker)
        echo "Starting Celery worker..."
        exec uv run celery -A [need_name] worker --loglevel=info
        ;;
    *)
        exec "$@"
        ;;
esac