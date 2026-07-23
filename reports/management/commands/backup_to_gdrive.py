import os
import tempfile
import json
import subprocess
from datetime import datetime
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    help = 'Backs up the database (SQLite or PostgreSQL) and uploads it to Google Drive'

    def handle(self, *args, **options):
        try:
            from googleapiclient.discovery import build
            from googleapiclient.http import MediaFileUpload
            from google.oauth2 import service_account
        except ImportError:
            self.stderr.write(
                "Error: Google API client libraries are not installed.\n"
                "Please run: pip install google-api-python-client google-auth\n"
                "and add them to requirements.txt"
            )
            return

        # 1. Load Configurations from environment variables
        gdrive_folder_id = os.environ.get('GDRIVE_FOLDER_ID')
        service_account_info_str = os.environ.get('GDRIVE_SERVICE_ACCOUNT_JSON')

        if not gdrive_folder_id:
            self.stderr.write("Error: GDRIVE_FOLDER_ID environment variable is not set.")
            return

        if not service_account_info_str:
            self.stderr.write("Error: GDRIVE_SERVICE_ACCOUNT_JSON environment variable (service account key json string) is not set.")
            return

        # 2. Authenticate with Google Drive API
        try:
            service_account_info = json.loads(service_account_info_str)
            creds = service_account.Credentials.from_service_account_info(
                service_account_info,
                scopes=['https://www.googleapis.com/auth/drive.file']
            )
            drive_service = build('drive', 'v3', credentials=creds)
        except Exception as e:
            self.stderr.write(f"Authentication failed: {e}")
            return

        # 3. Determine Database Type and Backup Source Path
        db_config = settings.DATABASES['default']
        db_engine = db_config['ENGINE']
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        backup_file_path = None
        file_name = None
        mimetype = None

        if 'sqlite3' in db_engine:
            # SQLite backup: Copy the database file
            db_file = db_config['NAME']
            if not os.path.exists(db_file):
                self.stderr.write(f"Error: SQLite database file not found at {db_file}")
                return
            
            backup_file_path = db_file
            file_name = f"backup_lms_db_{timestamp}.sqlite3"
            mimetype = 'application/x-sqlite3'
            self.stdout.write(f"Preparing SQLite database file: {file_name}")

        elif 'postgresql' in db_engine or 'postgis' in db_engine:
            # PostgreSQL backup: Run pg_dump to a temporary file
            temp_dir = tempfile.gettempdir()
            file_name = f"backup_lms_db_{timestamp}.sql"
            backup_file_path = os.path.join(temp_dir, file_name)
            mimetype = 'text/plain'

            self.stdout.write(f"Running pg_dump to generate: {file_name}")
            
            db_url = os.environ.get('DATABASE_URL')
            try:
                if db_url:
                    cmd = ['pg_dump', db_url, '-F', 'p', '-f', backup_file_path]
                else:
                    os.environ['PGPASSWORD'] = db_config.get('PASSWORD', '')
                    cmd = [
                        'pg_dump',
                        '-h', db_config.get('HOST', 'localhost'),
                        '-p', str(db_config.get('PORT', 5432)),
                        '-U', db_config.get('USER', 'postgres'),
                        '-F', 'p',
                        '-f', backup_file_path,
                        db_config.get('NAME')
                    ]
                
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                self.stdout.write("pg_dump completed successfully.")
            except Exception as e:
                self.stderr.write(f"pg_dump failed: {e}")
                if hasattr(e, 'stderr') and e.stderr:
                    self.stderr.write(e.stderr)
                return

        # 4. Upload File to Google Drive
        try:
            self.stdout.write(f"Uploading {file_name} to Google Drive folder: {gdrive_folder_id}...")
            
            file_metadata = {
                'name': file_name,
                'parents': [gdrive_folder_id]
            }
            media = MediaFileUpload(
                backup_file_path,
                mimetype=mimetype,
                resumable=True
            )
            
            uploaded_file = drive_service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, webViewLink'
            ).execute()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully backed up database!\n"
                    f"File ID: {uploaded_file.get('id')}\n"
                    f"Web Link: {uploaded_file.get('webViewLink')}"
                )
            )
        except Exception as e:
            self.stderr.write(f"Google Drive upload failed: {e}")
        finally:
            # Clean up the temporary pg_dump file
            if ('postgresql' in db_engine or 'postgis' in db_engine) and backup_file_path and os.path.exists(backup_file_path):
                os.remove(backup_file_path)
