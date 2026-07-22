from django.utils import timezone
from django.contrib.auth import logout
from django.contrib import messages
from django.shortcuts import redirect
from datetime import datetime

class SessionTimeoutMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated:
            now = timezone.now()
            
            # 1. Absolute login limit (9 hours = 32400 seconds)
            login_time_str = request.session.get('login_time')
            if login_time_str:
                try:
                    login_time = datetime.fromisoformat(login_time_str)
                    # Convert to aware if it is naive
                    if timezone.is_naive(login_time):
                        login_time = timezone.make_aware(login_time)
                    elapsed_since_login = (now - login_time).total_seconds()
                    if elapsed_since_login > 32400:  # 9 hours
                        logout(request)
                        messages.warning(request, "Your session has expired (maximum 9-hour limit reached). Please login again.")
                        return redirect('login')
                except Exception:
                    # In case of parsing error, reset login_time
                    request.session['login_time'] = now.isoformat()

            else:
                # Set it if not present
                request.session['login_time'] = now.isoformat()
            
            # 2. Inactivity limit (8 hours = 28800 seconds)
            last_activity_str = request.session.get('last_activity')
            if last_activity_str:
                try:
                    last_activity = datetime.fromisoformat(last_activity_str)
                    if timezone.is_naive(last_activity):
                        last_activity = timezone.make_aware(last_activity)
                    inactive_duration = (now - last_activity).total_seconds()
                    if inactive_duration > 28800:  # 8 hours
                        logout(request)
                        messages.warning(request, "You have been logged out due to 8 hours of inactivity.")
                        return redirect('login')
                except Exception:
                    # In case of parsing error, reset last_activity
                    request.session['last_activity'] = now.isoformat()
            else:
                request.session['last_activity'] = now.isoformat()
            
            # Update last activity
            request.session['last_activity'] = now.isoformat()
            
        response = self.get_response(request)
        return response
