#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Gather static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Create first admin user if no users exist (uses ADMIN_USERNAME / ADMIN_PASSWORD env vars)
python manage.py shell -c "
import os
from django.contrib.auth.models import User
username = os.environ.get('ADMIN_USERNAME', '')
password = os.environ.get('ADMIN_PASSWORD', '')
email = os.environ.get('ADMIN_EMAIL', 'admin@rmnihr.in')
if username and password:
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, email, password)
        print(f'Admin user [{username}] created successfully.')
    else:
        print(f'Admin user [{username}] already exists. Skipping.')
else:
    print('ADMIN_USERNAME or ADMIN_PASSWORD not set — skipping admin creation.')
"
