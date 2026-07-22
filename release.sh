#!/usr/bin/env bash
# Exit on error
set -o errexit

# Run migrations on the production database
python manage.py migrate

# Create or update the primary superuser in the production database
python manage.py create_superuser_rmnihr --force-update
