# Local Testing Guide - Authentication System

This guide helps you test all authentication changes locally before deploying to production.

## Setup Local Environment

### 1. Prepare Your Local Database

```bash
# Option A: Use SQLite for quick testing
# (Already configured in settings.py)
python manage.py migrate

# Option B: Use PostgreSQL locally (recommended for testing)
# First, install PostgreSQL locally

# Update DATABASE_URL for local testing
export DATABASE_URL=postgresql://username:password@localhost:5432/rmnihr_local

python manage.py migrate
```

### 2. Create Test Superuser

```bash
python manage.py create_superuser_rmnihr \
    --username rmnihr \
    --email bk.jha.3297@gmail.com \
    --password "Rmnihr@#virologyrhinmr1" \
    --passcode virology1
```

**Expected output:**
```
✓ Success: Created superuser account
  Username:     rmnihr
  Email:        bk.jha.3297@gmail.com
  Passcode:     virology1
  Status:       Active
```

### 3. Create Test Admin Account

```bash
python manage.py shell
```

Then in the shell:

```python
from django.contrib.auth.models import User
from reports.models import UserProfile

# Create test admin
admin_user = User.objects.create_user(
    username='testadmin',
    email='testadmin@rmnihr.in',
    password='TestAdmin@123456',
    is_staff=True,
    is_superuser=False
)

# Create profile
profile = UserProfile.objects.create(
    user=admin_user,
    is_admin_added_by_superadmin=True,
    is_super_admin=False
)

print(f"Created admin: {admin_user.username}")
exit()
```

---

## Test 1: Login Flows

### Test 1.1: Super Admin Login with Passcode

**Steps:**
1. Start server: `python manage.py runserver`
2. Visit: `http://localhost:8000/login/`
3. Click "Super Admin Login" tab
4. Enter:
   - Username: `rmnihr`
   - Password: `Rmnihr@#virologyrhinmr1`
   - Passcode: `virology1`
5. Click "Login"

**Expected Result:**
- ✓ Redirects to dashboard
- ✓ "Welcome" message appears
- ✓ User menu shows "rmnihr"

**Test Result:** _____ (PASS/FAIL)

---

### Test 1.2: Regular Admin Login

**Steps:**
1. Go to `http://localhost:8000/login/`
2. Stay on "Admin Login" tab (default)
3. Enter:
   - Username: `testadmin`
   - Password: `TestAdmin@123456`
4. Click "Login"

**Expected Result:**
- ✓ Redirects to dashboard
- ✓ User is logged in as testadmin

**Test Result:** _____ (PASS/FAIL)

---

### Test 1.3: Login by Email (Super Admin)

**Steps:**
1. Go to `http://localhost:8000/login/`
2. Click "Super Admin Login"
3. In Username field, enter: `bk.jha.3297@gmail.com`
4. Password: `Rmnihr@#virologyrhinmr1`
5. Passcode: `virology1`
6. Click "Login"

**Expected Result:**
- ✓ Redirects to dashboard
- ✓ Login resolves email to username correctly

**Test Result:** _____ (PASS/FAIL)

---

### Test 1.4: Invalid Credentials

**Steps:**
1. Go to `http://localhost:8000/login/`
2. Enter random username and password
3. Click "Login"

**Expected Result:**
- ✓ Shows error: "Invalid username/email or password."
- ✓ Stays on login page
- ✓ Form is not submitted

**Test Result:** _____ (PASS/FAIL)

---

### Test 1.5: Missing Passcode (Super Admin)

**Steps:**
1. Go to `http://localhost:8000/login/`
2. Click "Super Admin Login"
3. Enter username: `rmnihr`
4. Enter password: `Rmnihr@#virologyrhinmr1`
5. Leave passcode empty
6. Click "Login"

**Expected Result:**
- ✓ Shows error: "Invalid Super Admin passcode."
- ✓ Does not log in

**Test Result:** _____ (PASS/FAIL)

---

### Test 1.6: Wrong Passcode

**Steps:**
1. Same as above but enter wrong passcode (e.g., "wrong123")
2. Click "Login"

**Expected Result:**
- ✓ Shows error: "Invalid Super Admin passcode."

**Test Result:** _____ (PASS/FAIL)

---

## Test 2: Logout

### Test 2.1: Logout Button

**Steps:**
1. Login as super admin (see Test 1.1)
2. Click user menu dropdown (top right)
3. Click "Logout"

**Expected Result:**
- ✓ Redirects to login page
- ✓ Session is cleared
- ✓ Can't access dashboard without logging in again

**Test Result:** _____ (PASS/FAIL)

---

### Test 2.2: Session Access After Logout

**Steps:**
1. After logout, try to visit: `http://localhost:8000/dashboard/`

**Expected Result:**
- ✓ Redirects to login page
- ✓ Shows message: "Please log in to access this page"

**Test Result:** _____ (PASS/FAIL)

---

## Test 3: Password Reset (OTP Flow)

### Test 3.1: Step 1 - Request OTP

**Steps:**
1. Go to `http://localhost:8000/password-reset/`
2. Enter email: `bk.jha.3297@gmail.com`
3. Click "Send OTP"

**Expected Result:**
- ✓ Shows message: "OTP sent to your email"
- ✓ In development, OTP prints to console:
  ```
  ====================================================
  EMAIL (CONSOLE MODE):
  To: bk.jha.3297@gmail.com
  Subject: RMNIHR VRDL – Password Reset OTP
  
  Dear rmnihr,
  
  Your OTP for password reset is:
  
    123456
  ...
  ====================================================
  ```
- ✓ Page moves to Step 2 (OTP entry)

**Test Result:** _____ (PASS/FAIL)

---

### Test 3.2: Step 2 - Verify OTP

**Steps:**
1. After step 3.1, copy the OTP from console
2. On the form, enter the OTP
3. Click "Verify OTP"

**Expected Result:**
- ✓ OTP is accepted
- ✓ Page moves to Step 3 (password reset)

**Test Result:** _____ (PASS/FAIL)

---

### Test 3.3: Step 2 - Invalid OTP

**Steps:**
1. After step 3.1, enter wrong OTP (e.g., "000000")
2. Click "Verify OTP"

**Expected Result:**
- ✓ Shows error: "Invalid OTP. Please try again."
- ✓ Stays on Step 2

**Test Result:** _____ (PASS/FAIL)

---

### Test 3.4: Step 2 - Expired OTP

**Steps:**
1. Request OTP (step 3.1)
2. Wait 11 minutes (OTP expires after 10 minutes)
3. Enter the old OTP and try to verify

**Expected Result:**
- ✓ Shows error: "OTP has expired. Please request a new one."
- ✓ Page resets to Step 1

**Note:** For quick testing, you can modify the timeout in `password_reset_otp_view()`

**Test Result:** _____ (PASS/FAIL)

---

### Test 3.5: Step 3 - Reset Password

**Steps:**
1. Complete steps 3.1-3.2 successfully
2. On Step 3, enter:
   - New Username: `rmnihr_new`
   - New Email: `new.email@rmnihr.in`
   - New Password: `NewPassword@123456`
   - Confirm Password: `NewPassword@123456`
   - New Passcode (leave empty unless super admin): `newpasscode1`
3. Click "Reset Password"

**Expected Result:**
- ✓ Shows success message: "Password reset successful! You can now log in."
- ✓ Page resets to Step 1
- ✓ Can login with new credentials

**Test Result:** _____ (PASS/FAIL)

---

### Test 3.6: Step 3 - Password Mismatch

**Steps:**
1. Complete steps 3.1-3.2
2. On Step 3, enter passwords that don't match
3. Click "Reset Password"

**Expected Result:**
- ✓ Shows error: "Passwords do not match."
- ✓ Stays on Step 3

**Test Result:** _____ (PASS/FAIL)

---

### Test 3.7: Step 3 - Weak Password

**Steps:**
1. Complete steps 3.1-3.2
2. On Step 3, enter password with < 8 characters (e.g., "Pass123")
3. Click "Reset Password"

**Expected Result:**
- ✓ Shows error: "Password must be at least 8 characters."
- ✓ Stays on Step 3

**Test Result:** _____ (PASS/FAIL)

---

## Test 4: Admin Management

### Test 4.1: Create New Admin Account

**Steps:**
1. Login as super admin (`rmnihr`)
2. Go to `http://localhost:8000/super-admin/`
3. Click "Add Admin User"
4. Fill in:
   - Username: `newadmin`
   - Email: `newadmin@rmnihr.in`
   - Password: `NewAdmin@12345`
   - Confirm Password: `NewAdmin@12345`
5. Click "Add Admin"

**Expected Result:**
- ✓ Shows success: "Admin 'newadmin' successfully created!"
- ✓ Returns to admin list
- ✓ New admin appears in the list

**Test Result:** _____ (PASS/FAIL)

---

### Test 4.2: New Admin Can Login

**Steps:**
1. Logout as super admin
2. Login as new admin:
   - Username: `newadmin`
   - Password: `NewAdmin@12345`
3. Click "Login" (on Admin tab)

**Expected Result:**
- ✓ Redirects to dashboard
- ✓ User is logged in as `newadmin`

**Test Result:** _____ (PASS/FAIL)

---

### Test 4.3: Update Admin Profile

**Steps:**
1. Login as `rmnihr` (super admin)
2. Go to `http://localhost:8000/forgot-password/`
3. Update profile:
   - New Password: `UpdatedPassword@123456`
   - Confirm: `UpdatedPassword@123456`
4. Click "Update"

**Expected Result:**
- ✓ Shows success: "Account details successfully updated!"
- ✓ Session is maintained
- ✓ Can logout and login with new password

**Test Result:** _____ (PASS/FAIL)

---

## Test 5: Session Management

### Test 5.1: Session Persists Across Pages

**Steps:**
1. Login as super admin
2. Go to dashboard
3. Go to `/super-admin/`
4. Go to `/forgot-password/`
5. Go back to dashboard

**Expected Result:**
- ✓ Still logged in on all pages
- ✓ No login redirects
- ✓ User name visible in all pages

**Test Result:** _____ (PASS/FAIL)

---

### Test 5.2: Session Timeout Handling

**Note:** Session timeout is 9 hours, so full test is not practical for manual testing

**Steps:**
1. Login as super admin
2. Check `request.session['login_time']` in Django debug toolbar
3. Wait/simulate time passing
4. After 9 hours, session should expire

**Expected Result:**
- ✓ User is logged out after 9 hours of inactivity
- ✓ Redirected to login page

**Test Result:** _____ (PASS/FAIL)

---

## Test 6: Error Handling

### Test 6.1: Non-existent User Email

**Steps:**
1. Go to password reset: `http://localhost:8000/password-reset/`
2. Enter non-existent email: `nonexistent@example.com`
3. Click "Send OTP"

**Expected Result:**
- ✓ Shows error: "No account found with this email address."
- ✓ Stays on Step 1

**Test Result:** _____ (PASS/FAIL)

---

### Test 6.2: Invalid Email Format

**Steps:**
1. Go to password reset
2. Enter invalid email: `not.an.email`
3. Click "Send OTP"

**Expected Result:**
- ✓ Shows error: "Please provide a valid email address."

**Test Result:** _____ (PASS/FAIL)

---

### Test 6.3: Duplicate Username

**Steps:**
1. Login as super admin
2. Go to `/super-admin/` → "Add Admin User"
3. Try to create admin with existing username
4. Click "Add Admin"

**Expected Result:**
- ✓ Shows error: "Username already taken"

**Test Result:** _____ (PASS/FAIL)

---

## Test 7: Logging

### Test 7.1: Check Auth Logs

**Steps:**
1. Perform several login attempts (success and failure)
2. Check logs:
   ```bash
   tail -f logs/auth.log
   ```

**Expected Output:**
```
[INFO] 2026-07-22 10:30:45 reports.views [AUTH] LOGIN: rmnihr - success - Login type: super_admin
[INFO] 2026-07-22 10:31:10 reports.views [AUTH] LOGOUT: rmnihr - success
[WARNING] 2026-07-22 10:31:30 reports.views [AUTH] LOGIN: testadmin - failure - Password mismatch
```

**Test Result:** _____ (PASS/FAIL)

---

### Test 7.2: Check Email Logs

**Steps:**
1. Perform password reset
2. Check email logs:
   ```bash
   tail -f logs/email.log
   ```

**Expected Output:**
```
[INFO] 2026-07-22 10:35:00 reports.auth_utils Password reset OTP sent to bk.jha.3297@gmail.com
```

**Test Result:** _____ (PASS/FAIL)

---

## Test 8: URLs Check

Verify all authentication-related URLs work:

| URL | Expected | Result |
|-----|----------|--------|
| `/login/` | Login form loads | _____ |
| `/logout/` | Logs out and redirects | _____ |
| `/forgot-password/` | Profile page (requires login) | _____ |
| `/password-reset/` | OTP reset form loads | _____ |
| `/super-admin/` | Admin panel (requires superuser) | _____ |
| `/super-admin/admin/add/` | Add admin form | _____ |
| `/admin/` | Django admin (requires superuser) | _____ |

---

## Checklist Summary

### ✓ Core Functionality
- [ ] Super admin login works
- [ ] Regular admin login works
- [ ] Logout works
- [ ] Sessions persist
- [ ] Password reset OTP flow works

### ✓ Error Handling
- [ ] Invalid credentials show error
- [ ] Invalid OTP shows error
- [ ] Expired OTP shows error
- [ ] Weak password shows error
- [ ] Duplicate username shows error

### ✓ Admin Management
- [ ] Can create new admins
- [ ] New admins can login
- [ ] Can update profile
- [ ] Can change password

### ✓ Logging
- [ ] Auth logs are created
- [ ] Email logs are created
- [ ] Logs show relevant events
- [ ] No sensitive data in logs

### ✓ All URLs Work
- [ ] All authentication URLs accessible
- [ ] No 404 errors
- [ ] No 500 errors

---

## Performance Testing (Optional)

### Load Test Login

```bash
# Install Apache Bench (ab)
# On Mac: brew install httpd
# On Linux: apt-get install apache2-utils

# Test login endpoint (100 requests, 10 concurrent)
ab -n 100 -c 10 -X http://localhost:8000/login/

# Expected: < 200ms average response time
```

---

## Cleanup After Testing

```bash
# Remove test users
python manage.py shell
```

```python
from django.contrib.auth.models import User
User.objects.filter(username__in=['testadmin', 'newadmin', 'rmnihr_new']).delete()
exit()
```

---

## Sign-Off

- [ ] All tests passed
- [ ] No errors in logs
- [ ] Ready for production deployment

**Tested by:** ___________________  
**Date:** ___________________  
**Version Tested:** 1.0

---

**Last Updated:** 2026-07-22
