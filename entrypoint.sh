#!/bin/sh

echo "======================================"
echo "Starting KeviSeals Backend..."
echo "======================================"

python manage.py makemigrations

python manage.py migrate

exec "$@"