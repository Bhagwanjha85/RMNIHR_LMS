#!/usr/bin/env python
"""Django's command-line utility for administrative tasks."""
import os
import sys


def main():
    """Run administrative tasks."""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rmrims_reporting.settings')
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        import subprocess
        base_dir = os.path.dirname(os.path.abspath(__file__))
        fallback_success = False
        for env_name in ('.venv', 'venv', 'env'):
            venv_python_windows = os.path.normpath(os.path.join(base_dir, env_name, 'Scripts', 'python.exe'))
            venv_python_unix = os.path.normpath(os.path.join(base_dir, env_name, 'bin', 'python'))
            current_executable = os.path.normpath(sys.executable)
            
            if os.path.exists(venv_python_windows) and current_executable != venv_python_windows:
                sys.exit(subprocess.run([venv_python_windows] + sys.argv).returncode)
            elif os.path.exists(venv_python_unix) and current_executable != venv_python_unix:
                sys.exit(subprocess.run([venv_python_unix] + sys.argv).returncode)
        
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)


if __name__ == '__main__':
    main()
