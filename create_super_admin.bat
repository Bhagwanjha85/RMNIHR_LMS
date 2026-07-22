@echo off
echo Creating or updating a Super Admin...
.venv\Scripts\python.exe manage.py create_superuser_rmnihr --force-update
pause
