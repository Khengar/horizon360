#!/bin/bash
export DB_NAME=horizon_db
export DB_USER=horizon_user
export DB_PASSWORD=horizon_password
export DB_HOST=localhost
export CELERY_BROKER_URL=redis://localhost:6379/0

python manage.py runserver
