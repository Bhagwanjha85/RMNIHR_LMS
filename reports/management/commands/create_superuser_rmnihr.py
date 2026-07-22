"""
Django management command to create or update the primary superuser.

This command is essential for post-database-migration recovery when the auth_user
table has been wiped or migrated to a new database without preserving user data.

Can read from environment variables (for automated deployment):
    ADMIN_USERNAME, ADMIN_EMAIL, ADMIN_PASSWORD, ADMIN_PASSCODE

Or use command-line arguments (for manual runs):
    python manage.py create_superuser_rmnihr \
        --username rmnihr \
        --email bk.jha.3297@gmail.com \
        --password "Rmnihr@#virologyrhinmr1" \
        --passcode virology1
"""

from django.core.management.base import BaseCommand, CommandError
from django.contrib.auth.models import User
from reports.models import UserProfile
import logging
import os

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Create or update the primary superuser for RMNIHR VRDL system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--username',
            type=str,
            default=None,
            help='Username for the superuser (default: from ADMIN_USERNAME env var or "rmnihr")'
        )
        parser.add_argument(
            '--email',
            type=str,
            default=None,
            help='Email for the superuser (default: from ADMIN_EMAIL env var or "bk.jha.3297@gmail.com")'
        )
        parser.add_argument(
            '--password',
            type=str,
            default=None,
            help='Password for the superuser (default: from ADMIN_PASSWORD env var)'
        )
        parser.add_argument(
            '--passcode',
            type=str,
            default=None,
            help='Admin passcode for the superuser (default: from ADMIN_PASSCODE env var or "virology1")'
        )
        parser.add_argument(
            '--force-update',
            action='store_true',
            help='Force update existing superuser with new credentials'
        )

    def handle(self, *args, **options):
        # Read from environment variables first, then use CLI args as overrides
        username = options['username'] or os.environ.get('ADMIN_USERNAME', 'rmnihr')
        email = options['email'] or os.environ.get('ADMIN_EMAIL', 'bk.jha.3297@gmail.com')
        password = options['password'] or os.environ.get('ADMIN_PASSWORD', 'rmnihr@#virologyrhinmr')
        passcode = options['passcode'] or os.environ.get('ADMIN_PASSCODE', 'virology1')
        force_update = options['force_update']

        username = username.strip()
        email = email.strip()
        passcode = passcode.strip()

        try:
            self.stdout.write(
                f'\nCreating superuser...\n'
                f'   Source: {"Environment Variables" if os.environ.get("ADMIN_PASSWORD") else "CLI Arguments"}\n'
                f'   Username: {username}\n'
                f'   Email: {email}\n'
            )

            # Check if superuser already exists
            user = User.objects.filter(username=username).first()

            if user and not force_update:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Superuser "{username}" already exists. '
                        f'Use --force-update to update credentials.'
                    )
                )
                return

            if user and force_update:
                self.stdout.write(f'Updating existing superuser "{username}"...')
                user.email = email
                user.set_password(password)
                user.is_staff = True
                user.is_superuser = True
                user.is_active = True
                user.save()
                action = 'Updated'
            else:
                self.stdout.write(f'Creating new superuser "{username}"...')
                user = User.objects.create_user(
                    username=username,
                    email=email,
                    password=password,
                    is_staff=True,
                    is_superuser=True,
                    is_active=True
                )
                action = 'Created'

            # Create or update UserProfile
            profile, profile_created = UserProfile.objects.get_or_create(user=user)
            profile.is_super_admin = True
            profile.is_admin_added_by_superadmin = False
            profile.passcode = passcode
            profile.save()

            self.stdout.write(
                self.style.SUCCESS(
                    f'\nSuccess: {action} superuser account\n'
                    f'  Username:     {username}\n'
                    f'  Email:        {email}\n'
                    f'  Passcode:     {passcode}\n'
                    f'  Status:       Active\n'
                )
            )

            logger.info(
                f'Superuser "{username}" {action.lower()}. '
                f'Profile created: {profile_created}'
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error: {str(e)}')
            )
            logger.error(f'Failed to create superuser: {str(e)}', exc_info=True)
            raise CommandError(str(e))
