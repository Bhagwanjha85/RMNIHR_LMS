"""
Authentication utilities for RMNIHR VRDL system.

This module provides centralized authentication logic, logging, and error handling
for login, logout, password reset, and superuser management flows.

Attributes:
    logger: Configured logger for authentication events
"""

import logging
import random
import string
import json
import urllib.request
import urllib.error
import time
from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from django.conf import settings

logger = logging.getLogger(__name__)


def get_brevo_config():
    """
    Retrieve Brevo email configuration from Django settings.
    
    Returns:
        dict: Configuration with 'api_key' and 'from_email'
    """
    return {
        'api_key': getattr(settings, 'BREVO_SMTP_KEY', ''),
        'from_email': getattr(settings, 'BREVO_FROM_EMAIL', 'noreply@rmnihr.in'),
    }


def send_brevo_email(recipient_email, recipient_name, subject, message_text):
    """
    Send email via Brevo SMTP API using HTTP endpoint.
    
    This is more reliable than Django's built-in SMTP backend for OTP delivery.
    
    Args:
        recipient_email (str): Recipient's email address
        recipient_name (str): Recipient's display name
        subject (str): Email subject
        message_text (str): Plain text email body
        
    Returns:
        bool: True if successful, False otherwise
        
    Raises:
        Exception: If API call fails (HTTP error or network issue)
    """
    config = get_brevo_config()
    api_key = config['api_key']
    from_email = config['from_email']
    
    if not api_key:
        # Fallback: log to console for local development
        logger.warning(
            f'BREVO_SMTP_KEY not configured. Logging OTP to console:\n'
            f'To: {recipient_email}\n'
            f'Subject: {subject}\n'
            f'Body: {message_text}'
        )
        print(f'\n{"="*60}')
        print(f'EMAIL (CONSOLE MODE):')
        print(f'To: {recipient_email}')
        print(f'Subject: {subject}')
        print(f'{message_text}')
        print(f'{"="*60}\n')
        return True
    
    try:
        url = 'https://api.brevo.com/v3/smtp/email'
        headers = {
            'accept': 'application/json',
            'api-key': api_key,
            'content-type': 'application/json'
        }
        
        payload = {
            'sender': {
                'name': 'ICMR-RMNIHR VRDL',
                'email': from_email
            },
            'to': [
                {
                    'email': recipient_email,
                    'name': recipient_name
                }
            ],
            'subject': subject,
            'textContent': message_text
        }
        
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode('utf-8'),
            headers=headers,
            method='POST'
        )
        
        with urllib.request.urlopen(req, timeout=10) as response:
            response.read()
            logger.info(f'Email sent successfully to {recipient_email}')
            return True
            
    except urllib.error.HTTPError as e:
        error_body = e.read().decode('utf-8')
        logger.error(
            f'Brevo API error ({e.code}): {error_body}'
        )
        raise Exception(f'Brevo API error: {e.code} - {error_body}')
    except Exception as e:
        logger.error(f'Failed to send email via Brevo: {str(e)}')
        raise Exception(f'Failed to connect to Brevo API: {str(e)}')


def generate_otp(length=6):
    """Generate a random numeric OTP."""
    return ''.join(random.choices(string.digits, k=length))


def send_password_reset_otp(user, otp):
    """
    Send password reset OTP email to user.
    
    Args:
        user (User): Django User object
        otp (str): 6-digit OTP code
        
    Returns:
        bool: True if email sent successfully
    """
    subject = 'RMNIHR VRDL – Password Reset OTP'
    message = (
        f'Dear {user.get_full_name() or user.username},\n\n'
        f'Your OTP for password reset is:\n\n'
        f'  {otp}\n\n'
        f'This OTP expires in 10 minutes.\n'
        f'Do not share it with anyone.\n\n'
        f'– ICMR RMNIHR VRDL System'
    )
    
    try:
        send_brevo_email(
            recipient_email=user.email,
            recipient_name=user.get_full_name() or user.username,
            subject=subject,
            message_text=message
        )
        logger.info(f'Password reset OTP sent to {user.email} (user: {user.username})')
        return True
    except Exception as e:
        logger.error(f'Failed to send password reset OTP to {user.email}: {str(e)}')
        return False


def send_admin_login_otp(user, otp):
    """
    Send admin login verification OTP email to user.
    
    Args:
        user (User): Django User object
        otp (str): 6-digit OTP code
        
    Returns:
        bool: True if email sent successfully
    """
    subject = 'RMNIHR VRDL – Admin Login Verification OTP'
    message = (
        f'Dear {user.get_full_name() or user.username},\n\n'
        f'Your OTP for admin login verification is:\n\n'
        f'  {otp}\n\n'
        f'This OTP expires in 10 minutes.\n'
        f'Do not share it with anyone.\n\n'
        f'– ICMR RMNIHR VRDL System'
    )
    
    try:
        send_brevo_email(
            recipient_email=user.email,
            recipient_name=user.get_full_name() or user.username,
            subject=subject,
            message_text=message
        )
        logger.info(f'Admin login OTP sent to {user.email} (user: {user.username})')
        return True
    except Exception as e:
        logger.error(f'Failed to send admin login OTP to {user.email}: {str(e)}')
        return False


def mask_email(email):
    """
    Mask email address for display purposes.
    
    Example: 'user@example.com' -> 'us**@example.com'
    
    Args:
        email (str): Email address to mask
        
    Returns:
        str: Masked email address
    """
    if not email or '@' not in email:
        return email
    try:
        name, domain = email.split('@', 1)
        if len(name) > 4:
            masked_name = name[:4] + '*' * (len(name) - 4)
        else:
            masked_name = name[:2] + '*' * (len(name) - 2)
        return f'{masked_name}@{domain}'
    except Exception:
        return email


def resolve_user_by_username_or_email(username_or_email):
    """
    Resolve a user by username or email address.
    
    Args:
        username_or_email (str): Username or email address
        
    Returns:
        User or None: Django User object if found, None otherwise
    """
    if '@' in username_or_email:
        # Try email lookup
        user = User.objects.filter(email__iexact=username_or_email, is_active=True).first()
        if user:
            logger.debug(f'User resolved by email: {username_or_email}')
            return user
    
    # Try username lookup
    user = User.objects.filter(username__iexact=username_or_email, is_active=True).first()
    if user:
        logger.debug(f'User resolved by username: {username_or_email}')
        return user
    
    logger.warning(f'User not found: {username_or_email}')
    return None


def is_otp_expired(otp_created_at, max_age_seconds=600):
    """
    Check if OTP has expired.
    
    Args:
        otp_created_at (datetime): Timestamp when OTP was created
        max_age_seconds (int): Maximum OTP age in seconds (default: 600 = 10 minutes)
        
    Returns:
        bool: True if OTP is expired, False otherwise
    """
    if not otp_created_at:
        return True
    
    age_seconds = (timezone.now() - otp_created_at).total_seconds()
    return age_seconds > max_age_seconds


def log_authentication_event(event_type, user=None, username=None, status='success', details=''):
    """
    Log authentication events for audit trail.
    
    Args:
        event_type (str): Type of event (login, logout, password_reset, etc.)
        user (User): Django User object (optional)
        username (str): Username string (optional, used if user not provided)
        status (str): Status of event (success, failure)
        details (str): Additional details for the log
    """
    user_identifier = user.username if user else username
    log_message = f'[AUTH] {event_type.upper()}: {user_identifier} - {status}'
    if details:
        log_message += f' - {details}'
    
    if status == 'failure':
        logger.warning(log_message)
    else:
        logger.info(log_message)
