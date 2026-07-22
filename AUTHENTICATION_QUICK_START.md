# Quick Start: Authentication Recovery Guide

## Problem Summary

After migrating to Supabase PostgreSQL, your Django application cannot authenticate any users because the `auth_user` table is empty. **All users from the old database were not transferred to the new database.**

## Solution in 5 Steps

### Step 1: Create Primary Superuser (5 minutes)

Run this command in your project directory:

```bash
python manage.py create_superuser_rmnihr \
    --username rmnihr \
    --email bk.jha.3297@gmail.com \
    --password "Rmnihr@#virologyrhinmr1" \
    --passcode virology1
```

**Expected Output:**
```
✓ Success: Created superuser account
  Username:     rmnihr
  Email:        bk.jha.3297@gmail.com
  Passcode:     virology1
  Status:       Active
```

### Step 2: Verify Superuser (2 minutes)

Check if the superuser was created:

```bash
python manage.py shell
```

Then in the Python shell:

```python
from django.contrib.auth.models import User
from reports.models import UserProfile

# Check superuser exists
user = User.objects.get(username='rmnihr')
print(f"Username: {user.username}")
print(f"Email: {user.email}")
print(f"Is Superuser: {user.is_superuser}")
print(f"Is Staff: {user.is_staff}")

# Check profile
profile = user.profile
print(f"Is Super Admin: {profile.is_super_admin}")
print(f"Passcode: {profile.passcode}")

exit()
```

### Step 3: Test Login (2 minutes)

1. Start the development server:
   ```bash
   python manage.py runserver
   ```

2. Visit: `http://localhost:8000/login/`

3. Click the **"Super Admin Login"** tab

4. Enter:
   - **Username:** `rmnihr`
   - **Password:** `Rmnihr@#virologyrhinmr1`
   - **Passcode:** `virology1`

5. Click **Login**

**Expected Result:** You should see the dashboard with all reports

### Step 4: Create Additional Admin Users (5-10 minutes)

If you need other staff members to login:

1. Go to `/super-admin/` (Super Admin Panel)
2. Click "Add Admin User"
3. Fill in:
   - Username
   - Email
   - Password
   - Admin Passcode (if applicable)
4. Click "Add"

The new admin can now login at `/login/` under the "Admin Login" tab.

### Step 5: Restore Old User Data (If Available)

**If you have a backup of the old database:**

Export old data before migration (if not already done):

```bash
# If you still have access to old database
pg_dump old_database > old_data_backup.sql

# Load into new database
psql supabase_connection_string < old_data_backup.sql
```

Or using Django:

```bash
# Export from old database
python manage.py dumpdata auth.user reports.userprofile > users_export.json

# Import to new database
python manage.py loaddata users_export.json
```

---

## Testing Checklist

After completing steps 1-4, verify these work:

- [ ] **Login:** Super admin can login with passcode
- [ ] **Dashboard:** Can see all reports
- [ ] **Logout:** Logout works and returns to login page
- [ ] **Forgot Password:** Can access password reset page
- [ ] **Create Admin:** Can create new admin users
- [ ] **Admin Login:** New admin can login
- [ ] **Session:** Session persists when navigating pages

---

## Common Issues & Fixes

### "No User Found" Error During Login

**Problem:** You entered wrong credentials

**Fix:** Double-check:
- Username is exactly: `rmnihr` (lowercase)
- Password is exactly: `Rmnihr@#virologyrhinmr1`
- Passcode is exactly: `virology1` (no spaces)
- Using "Super Admin Login" tab (not regular Admin Login)

### "Could Not Send OTP" During Password Reset

**Problem:** Brevo email API not configured

**Fix:**
1. In your Render environment variables, verify `BREVO_SMTP_KEY` is set
2. Check that `BREVO_FROM_EMAIL` is set to your email
3. In development, OTP will print to console

### "Authentication Failed" After Login

**Problem:** Session not saving properly

**Fix:**
1. Ensure cookies are enabled in browser
2. Clear browser cache
3. Check that `SESSION_COOKIE_AGE` is set in settings (default: 9 hours)
4. Verify `DATABASES` is pointing to Supabase in settings

### Old User Accounts Still Don't Work

**Problem:** Old user data wasn't migrated

**Fix:** 
- Option A: Use the new superuser to recreate admin accounts
- Option B: Restore database backup if available
- Option C: Export old database and import to new one

---

## Command Reference

### Create/Update Superuser

```bash
# Create new superuser
python manage.py create_superuser_rmnihr \
    --username rmnihr \
    --email bk.jha.3297@gmail.com \
    --password "Rmnihr@#virologyrhinmr1" \
    --passcode virology1

# Update existing superuser
python manage.py create_superuser_rmnihr \
    --username rmnihr \
    --email new.email@example.com \
    --password "NewPassword123" \
    --passcode newpasscode \
    --force-update
```

### Check Database Connection

```bash
python manage.py dbshell
\dt  # List tables
SELECT COUNT(*) FROM auth_user;  # Count users
\q   # Quit
```

### View Logs

```bash
# On Linux/Mac:
tail -f logs/auth.log

# On Windows:
type logs\auth.log
```

---

## Before You Call for Help

Please verify:

1. [ ] Ran `python manage.py create_superuser_rmnihr` successfully
2. [ ] Database is Supabase (verify in settings.py `DATABASE_URL`)
3. [ ] Can see user in `python manage.py shell`:
   ```python
   User.objects.filter(username='rmnihr').exists()  # Should be True
   ```
4. [ ] `BREVO_SMTP_KEY` environment variable is set (for password reset)
5. [ ] Checked logs for error messages: `logs/auth.log`

---

## Next Steps

After recovering authentication:

1. **Restore user data** (if you have a backup)
2. **Create admin accounts** for your team
3. **Test all workflows** (login, logout, password reset)
4. **Set up monitoring** (check logs regularly)
5. **Document procedures** for your team

---

## Emergency Contact

If you need to reset everything:

1. Delete all users: `python manage.py shell`
   ```python
   from django.contrib.auth.models import User
   User.objects.all().delete()
   exit()
   ```

2. Run Step 1 again to create fresh superuser

3. Continue from Step 2

---

**Last Updated:** 2026-07-22  
**For:** RMNIHR VRDL System  
**Database:** Supabase PostgreSQL
