#!/usr/bin/env bash
# Render runs this on every deploy, before starting the app.
# Stop at the first failing command, so a broken build never goes live.
set -o errexit

pip install -r requirements.txt

# Gathers static files into STATIC_ROOT for WhiteNoise to serve.
python manage.py collectstatic --no-input

# Applies any new migrations to the production database.
python manage.py migrate
