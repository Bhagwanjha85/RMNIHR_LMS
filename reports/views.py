import json
from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.db.models import Q, Count
from django.utils import timezone
from django.http import HttpResponse
from .models import Report, ReportTest
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    # Clear any password reset OTP session variables when visiting the login page
    if request.method == 'GET':
        for k in ['otp_code', 'otp_email', 'otp_step', 'otp_time', 'otp_verified']:
            request.session.pop(k, None)
            
    error = None
    if request.method == 'POST':
        username_input = request.POST.get('username', '').strip()
        password_input = request.POST.get('password', '').strip()
        
        # Check if login input is an email, search for corresponding username
        username_to_auth = username_input
        if '@' in username_input:
            try:
                user_obj = User.objects.get(email=username_input)
                username_to_auth = user_obj.username
            except User.DoesNotExist:
                pass
                
        user = authenticate(request, username=username_to_auth, password=password_input)
        if user is not None:
            login(request, user)
            next_url = request.GET.get('next') or request.POST.get('next') or 'dashboard'
            return redirect(next_url)
        else:
            error = "Invalid username/email or password."
            
    return render(request, 'reports/login.html', {'error': error})

def logout_view(request):
    if request.method == 'POST' or request.method == 'GET':
        logout(request)
        return redirect('login')

@login_required
def forgot_password_view(request):
    error = None
    success = None
    if request.method == 'POST':
        new_username = request.POST.get('new_username')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        user = request.user
        
        # Reset/Change username if provided and different
        if new_username and new_username != user.username:
            if User.objects.filter(username=new_username).exclude(pk=user.pk).exists():
                error = "Username already taken by another account."
            else:
                user.username = new_username
        
        # Reset/Change password if provided
        if not error and new_password:
            if new_password != confirm_password:
                error = "Passwords do not match."
            else:
                user.set_password(new_password)
        
        if not error:
            user.save()
            # Update session hash to keep user logged in after password change
            from django.contrib.auth import update_session_auth_hash
            update_session_auth_hash(request, user)
            success = "Account details successfully updated!"
            
    return render(request, 'reports/forgot_password.html', {'error': error, 'success': success})


# ─── OTP Password Reset (accessible without login, for Brevo email OTP) ───
import random
import json
import urllib.request
import urllib.error
from django.conf import settings as django_settings

def send_brevo_otp_email(email, username, otp):
    key = getattr(django_settings, 'BREVO_SMTP_KEY', '')
    from_email = getattr(django_settings, 'BREVO_FROM_EMAIL', 'noreply@rmnihr.in')
    
    if key:
        url = 'https://api.brevo.com/v3/smtp/email'
        headers = {
            'accept': 'application/json',
            'api-key': key,
            'content-type': 'application/json'
        }
        data = {
            "sender": {
                "name": "ICMR-RMNIHR VRDL",
                "email": from_email
            },
            "to": [
                {
                    "email": email,
                    "name": username
                }
            ],
            "subject": "RMNIHR VRDL – Password Reset OTP",
            "textContent": (
                f"Dear {username},\n\n"
                f"Your OTP for password reset is:\n\n"
                f"  {otp}\n\n"
                f"This OTP expires in 10 minutes.\n"
                f"Do not share it with anyone.\n\n"
                f"– ICMR RMNIHR VRDL System"
            )
        }
        
        req = urllib.request.Request(
            url, 
            data=json.dumps(data).encode('utf-8'), 
            headers=headers, 
            method='POST'
        )
        try:
            with urllib.request.urlopen(req, timeout=10) as response:
                response.read()
        except urllib.error.HTTPError as e:
            error_body = e.read().decode('utf-8')
            raise Exception(f"Brevo API error: {e.code} - {error_body}")
        except Exception as e:
            raise Exception(f"Failed to connect to Brevo API: {str(e)}")
    else:
        # Console fallback for local testing
        print("\n" + "="*50)
        print("LOCAL DEVELOPER OTP EMAIL PREVIEW:")
        print(f"To: {email}")
        print(f"OTP Code: {otp}")
        print("="*50 + "\n")

def password_reset_otp_view(request):
    """3-step OTP password reset via Brevo SMTP/HTTP API. No login required."""
    if request.GET.get('reset') == '1':
        for k in ['otp_code', 'otp_email', 'otp_step', 'otp_time', 'otp_verified']:
            request.session.pop(k, None)
            
    step = request.session.get('otp_step', 1)
    error = None
    success = None

    if request.method == 'POST':
        action = request.POST.get('action', '')

        # ── STEP 1: Send OTP to email ──
        if action == 'send_otp':
            email = request.POST.get('email', '').strip()
            try:
                user = User.objects.get(email__iexact=email)
                otp = str(random.randint(100000, 999999))
                request.session['otp_code']  = otp
                request.session['otp_email'] = email
                request.session['otp_step']  = 2
                import time
                request.session['otp_time']  = int(time.time())

                # Send using the bulletproof Brevo HTTP API (Port 443)
                send_brevo_otp_email(
                    email=email,
                    username=user.get_full_name() or user.username,
                    otp=otp
                )
                step = 2
            except User.DoesNotExist:
                error = "No account found with this email address."
                step = 1
            except Exception as e:
                error = f"Could not send OTP. Please try again. ({str(e)[:80]})"
                step = 1

        # ── STEP 2: Verify OTP ──
        elif action == 'verify_otp':
            import time
            entered = request.POST.get('otp', '').strip()
            stored  = request.session.get('otp_code', '')
            sent_at = request.session.get('otp_time', 0)
            if int(time.time()) - sent_at > 600:  # 10 minutes
                error = "OTP has expired. Please request a new one."
                step = 1
                for k in ['otp_code', 'otp_email', 'otp_step', 'otp_time', 'otp_verified']:
                    request.session.pop(k, None)
            elif entered == stored:
                request.session['otp_verified'] = True
                request.session['otp_step'] = 3
                step = 3
            else:
                error = "Invalid OTP. Please try again."
                step = 2

        # ── STEP 3: Set new password ──
        elif action == 'reset_password':
            if request.session.get('otp_verified'):
                new_pw  = request.POST.get('new_password', '')
                conf_pw = request.POST.get('confirm_password', '')
                if len(new_pw) < 8:
                    error = "Password must be at least 8 characters."
                    step = 3
                elif new_pw != conf_pw:
                    error = "Passwords do not match."
                    step = 3
                else:
                    try:
                        user = User.objects.get(email=request.session.get('otp_email', ''))
                        user.set_password(new_pw)
                        user.save()
                        for k in ['otp_code', 'otp_email', 'otp_step', 'otp_time', 'otp_verified']:
                            request.session.pop(k, None)
                        success = "Password reset successful! You can now log in."
                        step = 1
                    except User.DoesNotExist:
                        error = "Session error. Please start again."
                        step = 1
            else:
                error = "Session expired. Please start again."
                step = 1

    return render(request, 'reports/password_reset_otp.html', {
        'step': step,
        'error': error,
        'success': success,
    })


@login_required
def dashboard(request):
    query = request.GET.get('q', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    test_filter = request.GET.get('test_filter', '')
    
    reports = Report.objects.prefetch_related('tests').all()
    
    if query:
        reports = reports.filter(
            Q(patient_name__icontains=query) |
            Q(lab_id__icontains=query) |
            Q(ref_by__icontains=query)
        )
        
    if start_date:
        reports = reports.filter(receiving_date__gte=start_date)
    if end_date:
        reports = reports.filter(receiving_date__lte=end_date)
        
    if test_filter:
        reports = reports.filter(tests__test_name=test_filter).distinct()
        
    # Get some quick analytics in a single optimized query using conditional aggregation
    # This avoids multiple nested subqueries (exclude pk__in) which slow down databases as they grow.
    stats = reports.annotate(
        is_pos=Count('tests', filter=Q(tests__interpretation_text='Positive')),
        is_eq=Count('tests', filter=Q(tests__interpretation_text='Equivocal')),
        is_neg=Count('tests', filter=Q(tests__interpretation_text='Negative'))
    ).aggregate(
        pos_cnt=Count('id', filter=Q(is_pos__gt=0)),
        eq_cnt=Count('id', filter=Q(is_pos=0, is_eq__gt=0)),
        neg_cnt=Count('id', filter=Q(is_pos=0, is_eq=0, is_neg__gt=0))
    )
    
    total_count = reports.count()
    positive_count = stats['pos_cnt']
    equivocal_count = stats['eq_cnt']
    negative_count = stats['neg_cnt']
    
    # Top tests run
    top_tests = ReportTest.objects.filter(report__in=reports).values('test_name').annotate(count=Count('id')).order_by('-count')
    top_tests_list = list(top_tests)[:5]
    
    # Build choices with selected flag so template needs no == comparison
    all_test_choices = [c[0] for c in ReportTest.TEST_CHOICES]
    test_choices = [(c, c == test_filter) for c in all_test_choices]

    from django.core.paginator import Paginator
    
    # Order before pagination
    reports = reports.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(reports, 20) # Show 20 reports per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'reports': page_obj,
        'page_obj': page_obj,
        'query': query,
        'start_date': start_date,
        'end_date': end_date,
        'test_filter': test_filter,
        'total_count': total_count,
        'positive_count': positive_count,
        'negative_count': negative_count,
        'equivocal_count': equivocal_count,
        'top_tests': top_tests_list,
        'test_choices': test_choices,
    }
    return render(request, 'reports/dashboard.html', context)

@login_required
def create_report(request):
    if request.method == 'POST':
        lab_id = request.POST.get('lab_id')
        sample_type = request.POST.get('sample_type', 'BLOOD')
        patient_name = request.POST.get('patient_name')
        receiving_date = request.POST.get('receiving_date')
        reporting_date = request.POST.get('reporting_date')
        age_value = request.POST.get('age_value')
        age_unit = request.POST.get('age_unit', 'Y')
        sex = request.POST.get('sex', 'F')
        ref_by = request.POST.get('ref_by', 'NMCH')
        test_method = request.POST.get('test_method', 'ELISA')
        notes = request.POST.get('notes')
        
        # Signatures
        show_prepared_by = request.POST.get('show_prepared_by') == 'on'
        show_technician = request.POST.get('show_technician') == 'on'
        show_scientist = request.POST.get('show_scientist') == 'on'
        show_vc = request.POST.get('show_vc') == 'on'
        
        prepared_by_name = request.POST.get('prepared_by_name', 'Report Prepared by')
        technician_name = request.POST.get('technician_name', 'Lab Technician / RA')
        scientist_name = request.POST.get('scientist_name', 'Research Scientist')
        vc_name = request.POST.get('vc_name', 'Dr. G.C Sahoo')
        vc_title = request.POST.get('vc_title', 'Signature of VC')
        
        # Tests data (JSON from dynamic frontend table)
        tests_data_json = request.POST.get('tests_data_json', '[]')
        
        try:
            with transaction.atomic():
                report = Report.objects.create(
                    lab_id=lab_id,
                    sample_type=sample_type,
                    patient_name=patient_name,
                    receiving_date=receiving_date or timezone.now().date(),
                    reporting_date=reporting_date or timezone.now().date(),
                    age_value=int(age_value or 0),
                    age_unit=age_unit,
                    sex=sex,
                    ref_by=ref_by,
                    test_method=test_method,
                    notes=notes,
                    show_prepared_by=show_prepared_by,
                    show_technician=show_technician,
                    show_scientist=show_scientist,
                    show_vc=show_vc,
                    prepared_by_name=prepared_by_name,
                    technician_name=technician_name,
                    scientist_name=scientist_name,
                    vc_name=vc_name,
                    vc_title=vc_title,
                )
                
                tests_list = json.loads(tests_data_json)
                for item in tests_list:
                    test_name = item.get('test_name')
                    result_value = item.get('result_value')
                    if test_name and result_value is not None:
                        ReportTest.objects.create(
                            report=report,
                            test_name=test_name,
                            result_value=result_value
                        )
                
                return redirect('view_report', pk=report.pk)
        except Exception as e:
            # Handle error
            return HttpResponse(f"Error creating report: {str(e)}", status=400)
            
    # GET request: render empty form
    all_test_choices = [c[0] for c in ReportTest.TEST_CHOICES]
    default_receiving_date = timezone.now().strftime('%Y-%m-%d')
    default_reporting_date = timezone.now().strftime('%Y-%m-%d')
    
    # Auto-generate next Lab ID if possible
    last_report = Report.objects.first()
    if last_report and last_report.lab_id.isdigit():
        next_lab_id = str(int(last_report.lab_id) + 1)
    else:
        next_lab_id = "4365"
        
    context = {
        'action': 'Create',
        'all_test_choices': all_test_choices,
        'default_receiving_date': default_receiving_date,
        'default_reporting_date': default_reporting_date,
        'next_lab_id': next_lab_id,
        'default_notes': "This report is not valid for any medico-legal purpose. Result reflect to the sample as received. Interpretation can be done by Clinician. Please contact the Lab for any clarification/re-evalutation of the result."
    }
    return render(request, 'reports/report_form.html', context)

@login_required
def edit_report(request, pk):
    report = get_object_or_404(Report, pk=pk)
    
    if request.method == 'POST':
        report.lab_id = request.POST.get('lab_id')
        report.sample_type = request.POST.get('sample_type', 'BLOOD')
        report.patient_name = request.POST.get('patient_name')
        report.receiving_date = request.POST.get('receiving_date')
        report.reporting_date = request.POST.get('reporting_date')
        report.age_value = int(request.POST.get('age_value') or 0)
        report.age_unit = request.POST.get('age_unit', 'Y')
        report.sex = request.POST.get('sex', 'F')
        report.ref_by = request.POST.get('ref_by', 'NMCH')
        report.test_method = request.POST.get('test_method', 'ELISA')
        report.notes = request.POST.get('notes')
        
        # Signatures
        report.show_prepared_by = request.POST.get('show_prepared_by') == 'on'
        report.show_technician = request.POST.get('show_technician') == 'on'
        report.show_scientist = request.POST.get('show_scientist') == 'on'
        report.show_vc = request.POST.get('show_vc') == 'on'
        
        report.prepared_by_name = request.POST.get('prepared_by_name')
        report.technician_name = request.POST.get('technician_name')
        report.scientist_name = request.POST.get('scientist_name')
        report.vc_name = request.POST.get('vc_name')
        report.vc_title = request.POST.get('vc_title')
        
        tests_data_json = request.POST.get('tests_data_json', '[]')
        
        try:
            with transaction.atomic():
                report.save()
                
                # Clear existing tests
                report.tests.all().delete()
                
                # Re-add tests
                tests_list = json.loads(tests_data_json)
                for item in tests_list:
                    test_name = item.get('test_name')
                    result_value = item.get('result_value')
                    if test_name and result_value is not None:
                        ReportTest.objects.create(
                            report=report,
                            test_name=test_name,
                            result_value=result_value
                        )
                
                return redirect('view_report', pk=report.pk)
        except Exception as e:
            return HttpResponse(f"Error updating report: {str(e)}", status=400)
            
    # GET request: pre-populate form
    all_test_choices = [c[0] for c in ReportTest.TEST_CHOICES]
    
    # Serialize existing tests for JavaScript
    existing_tests = []
    for test in report.tests.all():
        existing_tests.append({
            'test_name': test.test_name,
            'result_value': str(test.result_value)
        })
        
    context = {
        'action': 'Edit',
        'report': report,
        'existing_tests_json': json.dumps(existing_tests),
        'all_test_choices': all_test_choices,
        'default_receiving_date': report.receiving_date.strftime('%Y-%m-%d'),
        'default_reporting_date': report.reporting_date.strftime('%Y-%m-%d'),
    }
    return render(request, 'reports/report_form.html', context)

@login_required
def view_report(request, pk):
    report = get_object_or_404(Report.objects.prefetch_related('tests'), pk=pk)
    
    # Formatting dates to DD/MM/YYYY for the final printed report
    formatted_receiving_date = report.receiving_date.strftime('%d/%m/%Y')
    formatted_reporting_date = report.reporting_date.strftime('%d/%m/%Y')
    
    # Sex display mapping for clear label on PDF
    sex_map = {'M': 'MALE', 'F': 'FEMALE', 'O': 'OTHER'}
    sex_display = sex_map.get(report.sex, report.sex)
    
    context = {
        'report': report,
        'formatted_receiving_date': formatted_receiving_date,
        'formatted_reporting_date': formatted_reporting_date,
        'sex_display': sex_display,
    }
    return render(request, 'reports/report_print.html', context)

@login_required
def view_report_bw(request, pk):
    report = get_object_or_404(Report.objects.prefetch_related('tests'), pk=pk)
    formatted_receiving_date = report.receiving_date.strftime('%d/%m/%Y')
    formatted_reporting_date = report.reporting_date.strftime('%d/%m/%Y')
    sex_map = {'M': 'MALE', 'F': 'FEMALE', 'O': 'OTHER'}
    sex_display = sex_map.get(report.sex, report.sex)
    context = {
        'report': report,
        'formatted_receiving_date': formatted_receiving_date,
        'formatted_reporting_date': formatted_reporting_date,
        'sex_display': sex_display,
    }
    return render(request, 'reports/report_print_bw.html', context)

@login_required
def delete_report(request, pk):
    report = get_object_or_404(Report, pk=pk)
    if request.method == 'POST':
        report.delete()
        return redirect('dashboard')
    # If GET, show confirmation or redirect
    return render(request, 'reports/report_confirm_delete.html', {'report': report})

@login_required
def bulk_delete_reports(request):
    if request.method == 'POST':
        if request.POST.get('select_all_matching') == 'true':
            from django.db.models import Q
            query = request.POST.get('q', '')
            start_date = request.POST.get('start_date', '')
            end_date = request.POST.get('end_date', '')
            test_filter = request.POST.get('test_filter', '')
            
            reports = Report.objects.all()
            
            if query:
                reports = reports.filter(
                    Q(patient_name__icontains=query) |
                    Q(lab_id__icontains=query) |
                    Q(ref_by__icontains=query)
                )
            if start_date:
                reports = reports.filter(receiving_date__gte=start_date)
            if end_date:
                reports = reports.filter(receiving_date__lte=end_date)
            if test_filter:
                reports = reports.filter(tests__test_name=test_filter).distinct()
                
            reports.delete()
        else:
            report_ids = request.POST.getlist('report_ids')
            if report_ids:
                Report.objects.filter(pk__in=report_ids).delete()
        
        # Build redirect URL with parameters preserved
        from django.urls import reverse
        from urllib.parse import urlencode
        
        params = {}
        for key in ['q', 'start_date', 'end_date', 'test_filter']:
            val = request.POST.get(key)
            if val:
                params[key] = val
                
        redirect_url = reverse('dashboard')
        if params:
            redirect_url += '?' + urlencode(params)
        return redirect(redirect_url)
    return redirect('dashboard')

@login_required
def bulk_print_reports(request):
    if request.method == 'POST':
        from django.db.models import Q
        
        if request.POST.get('print_all') == 'true' or request.POST.get('select_all_matching') == 'true':
            query = request.POST.get('q', '')
            start_date = request.POST.get('start_date', '')
            end_date = request.POST.get('end_date', '')
            start_lab_id = request.POST.get('start_lab_id', '')
            end_lab_id = request.POST.get('end_lab_id', '')
            test_filter = request.POST.get('test_filter', '')
            
            reports = Report.objects.prefetch_related('tests').all()
            
            if query:
                reports = reports.filter(
                    Q(patient_name__icontains=query) |
                    Q(lab_id__icontains=query) |
                    Q(ref_by__icontains=query)
                )
            if start_date:
                reports = reports.filter(receiving_date__gte=start_date)
            if end_date:
                reports = reports.filter(receiving_date__lte=end_date)
            if start_lab_id:
                reports = reports.filter(lab_id__gte=start_lab_id)
            if end_lab_id:
                reports = reports.filter(lab_id__lte=end_lab_id)
            if test_filter:
                reports = reports.filter(tests__test_name=test_filter).distinct()
                
            reports = reports.order_by('-created_at')
            return render(request, 'reports/report_print_bulk.html', {'reports': reports})
        else:
            report_ids = request.POST.getlist('report_ids')
            if not report_ids:
                return redirect('dashboard')
                
            reports = Report.objects.filter(pk__in=report_ids).order_by('-created_at')
            return render(request, 'reports/report_print_bulk.html', {'reports': reports})
    return redirect('dashboard')

@login_required
def bulk_upload(request):
    if request.method == 'POST':
        if 'excel_file' in request.FILES:
            import openpyxl
            try:
                wb = openpyxl.load_workbook(request.FILES['excel_file'], data_only=True)
                sheet = wb.active
                rows = list(sheet.rows)
                if len(rows) > 1:
                    import re
                    import datetime
                    
                    # Normalize headers
                    headers = [re.sub(r'[^a-z0-9]', '', str(cell.value).lower()) if cell.value else '' for cell in rows[0]]
                    
                    # Mapping of Excel headers (normalized) to database choices
                    TEST_NAME_MAPPING = {
                        'hbsag': 'HBsAg',
                        'hcvantibodies': 'HCV Antibody',
                        'hcvantibody': 'HCV Antibody',
                        'havigm': 'HAV IgM',
                        'hevigm': 'HEV IgM',
                        'denigm': 'Dengue IgM',
                        'dengueigm': 'Dengue IgM',
                        'ns1': 'Dengue NS1',
                        'denguens1': 'Dengue NS1',
                        'chikunugyaigm': 'Chikungunya IgM',
                        'chikungunyaigm': 'Chikungunya IgM',
                        'leptospira': 'Leptospira',
                        'jeblood': 'JE IgM (Blood)',
                        'jeigmblood': 'JE IgM (Blood)',
                        'jecsf': 'JE IgM (CSF)',
                        'jeigmcsf': 'JE IgM (CSF)',
                        'st': 'Scrub Typhus (ST)',
                        'scrubtyphusst': 'Scrub Typhus (ST)',
                        'measles': 'Measles',
                        'mumps': 'Mumps',
                        'influenzah1n1': 'Influenza H1N1',
                        'influenzah3n2': 'Influenza H3N2',
                        'influenzavictoria': 'Influenza VICTORIA',
                    }
                    
                    metadata_fields = {
                        'labid', 'sampletype', 'patientname', 'receivingdate', 
                        'reportingdate', 'age', 'sex', 'refby', 'testmethod'
                    }

                    for row in rows[1:]:
                        data = {headers[i]: cell.value for i, cell in enumerate(row) if i < len(headers)}
                        if not any(data.values()):
                            continue
                        
                        # Parse age and age unit
                        age_raw = str(data.get('age', '') or '').strip().upper()
                        age_unit = 'Y'
                        if 'M' in age_raw:
                            age_unit = 'M'
                        elif 'D' in age_raw:
                            age_unit = 'D'
                        age_digits = re.sub(r'\D', '', age_raw)
                        parsed_age = int(age_digits) if age_digits else None
                        
                        # Parse sex
                        sex_raw = str(data.get('sex', 'F') or 'F').strip().upper()
                        if sex_raw.startswith('M'):
                            sex = 'M'
                        elif sex_raw.startswith('O'):
                            sex = 'O'
                        else:
                            sex = 'F'
                        
                        def parse_dt(val):
                            if isinstance(val, datetime.datetime):
                                return val.date()
                            if isinstance(val, datetime.date):
                                return val
                            if isinstance(val, str) and val.strip():
                                val_str = val.strip()
                                from django.utils.dateparse import parse_date
                                d = parse_date(val_str)
                                if d: return d
                                try:
                                    parts = val_str.replace('/', '-').split('-')
                                    if len(parts) == 3:
                                        if len(parts[0]) <= 2 and len(parts[2]) == 4:
                                            return datetime.date(int(parts[2]), int(parts[1]), int(parts[0]))
                                except:
                                    pass
                            return None
                            
                        recv_date = parse_dt(data.get('receivingdate'))
                        rep_date = parse_dt(data.get('reportingdate'))
                        
                        report_kwargs = {
                            'patient_name': str(data.get('patientname', '') or ''),
                            'lab_id': str(data.get('labid', '') or ''),
                            'age_value': parsed_age,
                            'age_unit': age_unit,
                            'sex': sex,
                            'ref_by': str(data.get('refby', '') or ''),
                            'sample_type': str(data.get('sampletype', 'BLOOD') or 'BLOOD'),
                            'test_method': str(data.get('testmethod', 'ELISA') or 'ELISA'),
                            'show_prepared_by': False,
                            'show_technician': False,
                            'show_scientist': False,
                            'show_vc': False,
                        }
                        if recv_date:
                            report_kwargs['receiving_date'] = recv_date
                        if rep_date:
                            report_kwargs['reporting_date'] = rep_date
                            
                        report = Report.objects.create(**report_kwargs)
                        
                        # Process individual test columns (from column J/index 9 onwards)
                        for i, cell in enumerate(row):
                            if i >= len(headers):
                                break
                            header_normalized = headers[i]
                            if not header_normalized or header_normalized in metadata_fields:
                                continue
                            
                            val = cell.value
                            if val is not None:
                                val_str = str(val).strip()
                                if val_str:  # Only add if the cell is not empty
                                    test_name_db = TEST_NAME_MAPPING.get(header_normalized, str(rows[0][i].value).strip())
                                    ReportTest.objects.create(
                                        report=report,
                                        test_name=test_name_db,
                                        result_value=val_str
                                    )
                                    
                return redirect('dashboard')
            except Exception as e:
                return HttpResponse(f"Error processing file: {str(e)}", status=400)
    return render(request, 'reports/bulk_upload.html')

@login_required
def export_reports_excel(request):
    from django.db.models import Q
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
    
    query = request.GET.get('q', '')
    start_date = request.GET.get('start_date', '')
    end_date = request.GET.get('end_date', '')
    test_filter = request.GET.get('test_filter', '')
    
    reports = Report.objects.prefetch_related('tests').all()
    
    if query:
        reports = reports.filter(
            Q(patient_name__icontains=query) |
            Q(lab_id__icontains=query) |
            Q(ref_by__icontains=query)
        )
    if start_date:
        reports = reports.filter(receiving_date__gte=start_date)
    if end_date:
        reports = reports.filter(receiving_date__lte=end_date)
    if test_filter:
        reports = reports.filter(tests__test_name=test_filter).distinct()
        
    reports = reports.order_by('-created_at')
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Reports"
    
    meta_headers = [
        "Lab ID", "Patient Name", "Age", "Age Unit", "Sex", 
        "Ref By", "Sample Type", "Test Method", "Receiving Date", "Reporting Date"
    ]
    
    unique_tests = sorted(list(set(
        ReportTest.objects.filter(report__in=reports).values_list('test_name', flat=True)
    )))
    
    headers = meta_headers + unique_tests
    
    header_fill = PatternFill(start_color="1B285C", end_color="1B285C", fill_type="solid")
    header_font = Font(name="Arial", size=11, bold=True, color="FFFFFF")
    center_align = Alignment(horizontal="center", vertical="center")
    left_align = Alignment(horizontal="left", vertical="center")
    
    ws.append(headers)
    for col_idx in range(1, len(headers) + 1):
        cell = ws.cell(row=1, column=col_idx)
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = center_align
        
    thin_border = Border(
        left=Side(style='thin', color='DDDDDD'),
        right=Side(style='thin', color='DDDDDD'),
        top=Side(style='thin', color='DDDDDD'),
        bottom=Side(style='thin', color='DDDDDD')
    )
    
    for r_idx, report in enumerate(reports, start=2):
        sex_map = {'M': 'Male', 'F': 'Female', 'O': 'Other'}
        sex_str = sex_map.get(report.sex, report.sex or '')
        
        recv_str = report.receiving_date.strftime('%Y-%m-%d') if report.receiving_date else ""
        rep_str = report.reporting_date.strftime('%Y-%m-%d') if report.reporting_date else ""
        
        row_values = [
            report.lab_id or "",
            report.patient_name or "",
            report.age_value or "",
            report.get_age_unit_display() if report.age_value else "",
            sex_str,
            report.ref_by or "",
            report.sample_type or "",
            report.test_method or "",
            recv_str,
            rep_str
        ]
        
        test_results = {t.test_name: t.result_value for t in report.tests.all()}
        for test in unique_tests:
            row_values.append(test_results.get(test, ""))
            
        ws.append(row_values)
        
        for col_idx in range(1, len(headers) + 1):
            cell = ws.cell(row=r_idx, column=col_idx)
            cell.alignment = left_align if col_idx == 2 else center_align
            cell.border = thin_border
            cell.font = Font(name="Arial", size=10)
            
    for col in ws.columns:
        max_len = 0
        col_letter = openpyxl.utils.get_column_letter(col[0].column)
        for cell in col:
            val = str(cell.value or '')
            if len(val) > max_len:
                max_len = len(val)
        ws.column_dimensions[col_letter].width = max(max_len + 3, 12)
        
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response['Content-Disposition'] = f'attachment; filename="reports_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.xlsx"'
    wb.save(response)
    return response


