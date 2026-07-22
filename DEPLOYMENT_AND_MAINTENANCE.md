# Deployment and Maintenance Guide

## Overview

This guide covers deploying the RMNIHR VRDL system with the new authentication system to Render and maintaining it in production.

---

## Pre-Deployment Checklist

### 1. Local Testing (Do This First!)

```bash
# 1a. Create fresh superuser locally
python manage.py create_superuser_rmnihr \
    --username rmnihr \
    --email bk.jha.3297@gmail.com \
    --password "Rmnihr@#virologyrhinmr1" \
    --passcode virology1

# 1b. Test login locally
python manage.py runserver
# Visit http://localhost:8000/login/
# Test login with credentials above

# 1c. Test password reset flow
# Visit http://localhost:8000/password-reset/
# Enter your email and verify OTP flow (will print to console in dev)

# 1d. Collect static files
python manage.py collectstatic --noinput

# 1e. Check for any errors
python manage.py check
```

### 2. Environment Variables Setup

Ensure these are configured in your Render environment:

**Required:**
```
DATABASE_URL=postgresql://user:pass@supabase.co/dbname
BREVO_SMTP_KEY=your-brevo-api-key
BREVO_FROM_EMAIL=your-email@rmnihr.in
SECRET_KEY=your-very-long-secret-key
DEBUG=False
```

**Optional (but recommended):**
```
ALLOWED_HOSTS=yourdomain.com,www.yourdomain.com,yourdomain.onrender.com
LOG_LEVEL=INFO
```

### 3. Database Configuration

**In Supabase:**

```sql
-- Verify tables exist
\dt

-- Check auth_user table
SELECT COUNT(*) FROM auth_user;

-- Verify you can connect
SELECT version();
```

**In settings.py (already done):**
- ✓ `dj_database_url` configured
- ✓ SSL mode set to 'require' for PostgreSQL
- ✓ Connection health checks enabled

---

## Deployment Steps

### Step 1: Push Code to GitHub

```bash
git add .
git commit -m "Fix: Implement authentication system with OTP recovery"
git push origin main
```

### Step 2: Trigger Render Deployment

1. Go to https://dashboard.render.com/
2. Select your service
3. Go to "Manual Deploy" → "Deploy latest commit"
4. Wait for build to complete (10-15 minutes)

### Step 3: Run Migrations

In Render's shell (if available) or via SSH:

```bash
# SSH into Render instance or use Web Console
python manage.py migrate

# Create superuser
python manage.py create_superuser_rmnihr \
    --username rmnihr \
    --email bk.jha.3297@gmail.com \
    --password "Rmnihr@#virologyrhinmr1" \
    --passcode virology1
```

**Or use Render's pre-deploy commands:**

In `render.yaml` or Render dashboard's "Pre-deploy command":

```bash
python manage.py migrate && \
python manage.py collectstatic --noinput
```

### Step 4: Verify Deployment

1. Visit https://yourdomain.onrender.com/login/
2. Super admin login:
   - Username: `rmnihr`
   - Password: `Rmnihr@#virologyrhinmr1`
   - Passcode: `virology1`
3. Test dashboard access
4. Test logout

---

## Post-Deployment: Create Initial Admin Accounts

### Create Staff Admin Accounts

1. Login as super admin (`rmnihr`)
2. Go to `/super-admin/`
3. Click "Add Admin User"
4. Fill in details for each staff member
5. Share login credentials securely

**Example admin creation:**
```
Username: dr_patel
Email: patel@rmnihr.in
Password: SecurePass123!
```

---

## Monitoring and Maintenance

### Daily Checks

```bash
# Check logs for errors
tail -f logs/auth.log
tail -f logs/email.log

# Monitor database connection
python manage.py dbshell
SELECT COUNT(*) FROM auth_user;  # Should be >= 1
```

### Weekly Tasks

1. **Review Authentication Logs:**
   - Check for failed login attempts
   - Look for suspicious patterns
   - Monitor OTP delivery issues

2. **Verify Backups:**
   - Confirm Supabase automated backups are running
   - Test restore procedure periodically

3. **Update Admin List:**
   - Remove inactive accounts
   - Add new staff members

### Monthly Tasks

1. **Security Review:**
   - Change superuser password if needed: `python manage.py create_superuser_rmnihr --force-update --password "NewPassword123"`
   - Audit admin accounts
   - Review session logs

2. **Performance Check:**
   - Monitor login page response time
   - Check email delivery success rate
   - Review database performance

---

## Troubleshooting in Production

### Issue: Login Page Shows "Database Connection Error"

```bash
# Check database connectivity
python manage.py dbshell

# If that fails, verify DATABASE_URL
echo $DATABASE_URL

# Check SSL certificate
psql -d "your_database_url" -c "SELECT 1;"
```

**Fix:**
- Verify Supabase database is running
- Check DATABASE_URL format (should include `?sslmode=require`)
- Ensure firewall allows connections

### Issue: Password Reset OTP Not Sent

```bash
# Check Brevo configuration
echo $BREVO_SMTP_KEY
echo $BREVO_FROM_EMAIL

# Test API connection
curl -X GET "https://api.brevo.com/v3/account" \
  -H "api-key: $BREVO_SMTP_KEY"
```

**Fix:**
- Verify BREVO_SMTP_KEY is set correctly
- Check email provider dashboard for rate limits
- Verify sender email is authorized
- Review logs: `tail -f logs/email.log`

### Issue: Sessions Expire Too Quickly

**Current setting:** 9 hours (32400 seconds)

**To change:**
```python
# In rmrims_reporting/settings.py
SESSION_COOKIE_AGE = 32400  # Change this value (in seconds)
```

### Issue: User Can't Login Despite Correct Credentials

```bash
# Debug in shell
python manage.py shell

from django.contrib.auth.models import User
from django.contrib.auth import authenticate

user = User.objects.get(username='rmnihr')
print(f"User exists: {user.username}")
print(f"Is active: {user.is_active}")
print(f"Is superuser: {user.is_superuser}")

# Test authentication
auth_user = authenticate(username='rmnihr', password='Rmnihr@#virologyrhinmr1')
print(f"Authentication result: {auth_user}")

exit()
```

---

## Backup and Recovery

### Regular Backups

**Supabase automatically backs up your database.**

To verify:
1. Go to Supabase Dashboard
2. Project Settings → Backups
3. You should see scheduled backups

### Manual Backup (for export)

```bash
# Export database
pg_dump "your_database_url" > rmnihr_backup_$(date +%Y%m%d).sql

# Export to file with compression
pg_dump "your_database_url" | gzip > rmnihr_backup_$(date +%Y%m%d).sql.gz
```

### Emergency Recovery

**If database is corrupted:**

1. Go to Supabase Dashboard
2. Database → Backups
3. Click "Restore" on a previous backup
4. Confirm restoration
5. Verify data integrity

---

## Scaling Considerations

### User Load

As user count grows:

1. **Database indexes:** Verify indexes on `auth_user.username` and `auth_user.email`
   ```sql
   CREATE INDEX idx_auth_user_username ON auth_user(username);
   CREATE INDEX idx_auth_user_email ON auth_user(email);
   ```

2. **Session management:** Use cache for session data
   ```python
   # In settings.py
   SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
   CACHES = {
       'default': {
           'BACKEND': 'django.core.cache.backends.redis.RedisCache',
           'LOCATION': 'redis://redis_host:6379/1',
       }
   }
   ```

3. **Email throughput:** Monitor Brevo usage
   - Brevo free tier: 300 emails/day
   - Check usage at: https://app.brevo.com/dashboard/stats/emails

### Database Performance

Monitor these metrics in Supabase:

1. Connection count
2. Query performance
3. Disk usage
4. CPU usage

**Optimization tips:**
- Add indexes on frequently queried columns
- Use database connection pooling
- Archive old logs periodically

---

## Security Best Practices

### Password Security

1. **Superuser password:**
   - Change immediately after initial setup
   - Use strong password (16+ characters, mix of types)
   - Never commit to GitHub

2. **Admin passwords:**
   - Enforce minimum 12 characters
   - Require special characters
   - Expire periodically (every 90 days)

### API Security

1. **Brevo API key:**
   - Store only in environment variables
   - Rotate annually
   - Monitor usage for anomalies

2. **Session security:**
   - Ensure HTTPS only (set `SESSION_COOKIE_SECURE = True`)
   - Set `SESSION_COOKIE_HTTPONLY = True`
   - Use secure cookie age

3. **CSRF Protection:**
   - Verify `CSRF_TRUSTED_ORIGINS` in settings
   - Test form submissions from different domains

---

## Disaster Recovery Plan

### Database Loss

**If entire database is lost:**

1. Restore from Supabase backup (see above)
2. Or recreate from scratch:
   ```bash
   python manage.py migrate
   python manage.py create_superuser_rmnihr \
       --username rmnihr \
       --email bk.jha.3297@gmail.com \
       --password "Rmnihr@#virologyrhinmr1" \
       --passcode virology1
   ```

### Service Downtime

1. Check Render dashboard for status
2. Restart service: Dashboard → Web Service → Restart
3. If persistent, check logs for errors
4. Rollback to previous deployment if needed

### Forgotten Superuser Password

```bash
# Create new superuser (this overwrites existing)
python manage.py create_superuser_rmnihr \
    --username rmnihr \
    --password "NewPassword123" \
    --force-update
```

---

## Performance Optimization

### Database Queries

Avoid N+1 queries in templates:

```python
# ✗ Bad - queries for every report
for report in reports:
    created_by = report.created_by.username

# ✓ Good - single query with select_related
reports = Report.objects.select_related('created_by')
for report in reports:
    created_by = report.created_by.username
```

### Cache Configuration

```python
# In settings.py - add caching for login
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}
```

### Static Files

Already configured with WhiteNoise and compression.

---

## Support and Documentation

### Logs Location

- Authentication logs: `logs/auth.log`
- Email logs: `logs/email.log`
- Django logs: Check Render dashboard

### Internal Documentation

- `AUTHENTICATION_FIX.md` - Detailed technical explanation
- `AUTHENTICATION_QUICK_START.md` - Quick recovery steps
- `DEPLOYMENT_AND_MAINTENANCE.md` - This file
- `README.md` - General project documentation

### External Resources

- Django Docs: https://docs.djangoproject.com/
- Brevo Docs: https://developers.brevo.com/
- Supabase Docs: https://supabase.com/docs

---

## Rollback Procedure

If deployment introduces issues:

### Option 1: Render Dashboard Rollback

1. Go to Render Dashboard
2. Select your service
3. Go to "Deploys"
4. Click "Rollback" on previous successful deploy
5. Confirm and wait for redeploy

### Option 2: Manual Rollback

```bash
git revert HEAD  # Revert last commit
git push origin main
# Trigger redeploy via Render dashboard
```

---

## Maintenance Schedule

| Task | Frequency | Owner | Notes |
|------|-----------|-------|-------|
| Review auth logs | Daily | Admin | Check for errors/suspicious activity |
| Verify backups | Weekly | Admin | Ensure Supabase backups are running |
| Test password reset | Weekly | Admin | Verify email delivery |
| Update admin accounts | Monthly | Super Admin | Add/remove staff |
| Security audit | Monthly | Super Admin | Review permissions and logs |
| Database optimization | Quarterly | DBA | Monitor performance, add indexes |
| Change superuser password | Quarterly | Super Admin | For security |

---

## Emergency Contacts

Keep this information secure:

- **Primary Admin Email:** bk.jha.3297@gmail.com
- **Brevo Support:** support@brevo.com
- **Supabase Support:** https://supabase.com/support
- **Render Support:** https://render.com/support

---

**Last Updated:** 2026-07-22  
**Version:** 1.0  
**Environment:** Production Render + Supabase
