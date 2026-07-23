from django.apps import AppConfig


class ReportsConfig(AppConfig):
    name = 'reports'

    def ready(self):
        try:
            from django.db import connection
            if 'reports_testconfig' in connection.introspection.table_names():
                from reports.backup_utils import restore_test_configs_from_backup_if_needed
                restore_test_configs_from_backup_if_needed()
        except Exception:
            pass

