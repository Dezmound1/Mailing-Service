#!/bin/sh
set -e

COMMAND="${1:-web}"
cd mailing_service

run_migrations() {
    echo "Running migrations..."
    uv run python manage.py migrate --noinput
}

case "$COMMAND" in
    web)
        run_migrations
        
        echo "Creating superuser (if not exists)..."
        uv run python manage.py createsuperuser --noinput 2>/dev/null || true

        echo "Starting Django development server..."
        exec uv run python manage.py runserver 0.0.0.0:8000
        ;;
    worker)
        echo "Starting Celery worker..."
        exec uv run celery -A mailing_service worker --loglevel=info
        ;;
    *)
        exec "$@"
        ;;
esac
