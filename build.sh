#!/usr/bin/env bash
# Exit on error
set -o errexit

# Install dependencies
pip install -r requirements.txt

# Gather static files
python manage.py collectstatic --noinput

# Run migrations
python manage.py migrate

# Create or update admin user (always syncs password from env vars or defaults)
python manage.py shell -c "
import os
from django.contrib.auth.models import User
username = os.environ.get('ADMIN_USERNAME', 'admin')
password = os.environ.get('ADMIN_PASSWORD', 'AdminPassword123')
email    = os.environ.get('ADMIN_EMAIL', 'bk.jha.3297@gmail.com')
if username and password:
    user, created = User.objects.get_or_create(username=username)
    user.email       = email
    user.is_staff    = True
    user.is_superuser = True
    user.set_password(password)
    user.save()
    action = 'created' if created else 'updated'
    print(f'Admin user [{username}] {action} successfully with email {email}.')
else:
    print('ADMIN_USERNAME or ADMIN_PASSWORD not set — skipping admin setup.')
"

