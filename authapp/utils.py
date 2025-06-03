# type: ignore
# authapp/utils.py
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_verification_email(user, verification_code):
    """
    Send email verification code to user
    """
    subject = 'Verify Your Account - Streaming Platform'
    
    # Create HTML content
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Email Verification</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 10px 10px 0 0;
            }}
            .content {{
                background: #f9f9f9;
                padding: 30px;
                border-radius: 0 0 10px 10px;
            }}
            .verification-code {{
                background: #667eea;
                color: white;
                font-size: 24px;
                font-weight: bold;
                text-align: center;
                padding: 20px;
                margin: 20px 0;
                border-radius: 5px;
                letter-spacing: 3px;
            }}
            .footer {{
                text-align: center;
                color: #666;
                margin-top: 20px;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Welcome to Our Streaming Platform!</h1>
        </div>
        <div class="content">
            <h2>Hi {user.first_name},</h2>
            <p>Thank you for signing up! To complete your registration, please verify your email address using the verification code below:</p>
            
            <div class="verification-code">
                {verification_code}
            </div>
            
            <p>This code will expire in 30 minutes for security reasons.</p>
            
            <p>If you didn't create an account with us, you can safely ignore this email.</p>
            
            <p>Welcome aboard!<br>
            The Streaming Platform Team</p>
        </div>
        <div class="footer">
            <p>This is an automated message, please do not reply to this email.</p>
        </div>
    </body>
    </html>
    """
    
    plain_message = f"""
    Hi {user.first_name},
    
    Thank you for signing up for our Streaming Platform!
    
    To complete your registration, please verify your email address using this verification code:
    
    {verification_code}
    
    This code will expire in 30 minutes.
    
    If you didn't create an account with us, you can safely ignore this email.
    
    Welcome aboard!
    The Streaming Platform Team
    """
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Verification email sent successfully to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send verification email to {user.email}: {str(e)}")
        return False

def send_password_reset_email(user, reset_code):
    """
    Send password reset code to user
    """
    subject = 'Reset Your Password - Streaming Platform'
    
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Password Reset</title>
        <style>
            body {{
                font-family: Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
            }}
            .header {{
                background: linear-gradient(135deg, #ff6b6b 0%, #ffa726 100%);
                color: white;
                padding: 30px;
                text-align: center;
                border-radius: 10px 10px 0 0;
            }}
            .content {{
                background: #f9f9f9;
                padding: 30px;
                border-radius: 0 0 10px 10px;
            }}
            .reset-code {{
                background: #ff6b6b;
                color: white;
                font-size: 24px;
                font-weight: bold;
                text-align: center;
                padding: 20px;
                margin: 20px 0;
                border-radius: 5px;
                letter-spacing: 3px;
            }}
            .footer {{
                text-align: center;
                color: #666;
                margin-top: 20px;
                font-size: 14px;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>Password Reset Request</h1>
        </div>
        <div class="content">
            <h2>Hi {user.first_name},</h2>
            <p>We received a request to reset your password. Use the code below to reset your password:</p>
            
            <div class="reset-code">
                {reset_code}
            </div>
            
            <p>This code will expire in 30 minutes for security reasons.</p>
            
            <p>If you didn't request a password reset, you can safely ignore this email. Your password will remain unchanged.</p>
            
            <p>Best regards,<br>
            The Streaming Platform Team</p>
        </div>
        <div class="footer">
            <p>This is an automated message, please do not reply to this email.</p>
        </div>
    </body>
    </html>
    """
    
    plain_message = f"""
    Hi {user.first_name},
    
    We received a request to reset your password for your Streaming Platform account.
    
    Use this code to reset your password:
    
    {reset_code}
    
    This code will expire in 30 minutes.
    
    If you didn't request a password reset, you can safely ignore this email.
    
    Best regards,
    The Streaming Platform Team
    """
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            html_message=html_message,
            fail_silently=False,
        )
        logger.info(f"Password reset email sent successfully to {user.email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send password reset email to {user.email}: {str(e)}")
        return False

def log_user_activity(user, activity_type, description="", request=None, extra_data=None):
    """
    Log user activity for tracking and analytics
    """
    from .models import UserActivity
    
    ip_address = None
    user_agent = ""
    
    if request:
        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        # Get user agent
        user_agent = request.META.get('HTTP_USER_AGENT', '')
    
    try:
        UserActivity.objects.create(
            user=user,
            activity_type=activity_type,
            description=description,
            ip_address=ip_address,
            user_agent=user_agent,
            extra_data=extra_data or {}
        )
        logger.info(f"Logged activity: {user.email} - {activity_type}")
    except Exception as e:
        logger.error(f"Failed to log user activity: {str(e)}")

def generate_username_from_email(email):
    """
    Generate a unique username from email
    """
    from .models import User
    
    base_username = email.split('@')[0]
    username = base_username
    counter = 1
    
    while User.objects.filter(username=username).exists():
        username = f"{base_username}{counter}"
        counter += 1
    
    return username

def validate_file_upload(file, allowed_types=None, max_size=None):
    """
    Validate uploaded files
    """
    if not file:
        return False, "No file provided"
    
    # Check file size
    if max_size and file.size > max_size:
        return False, f"File size exceeds maximum allowed size of {max_size} bytes"
    
    # Check file type
    if allowed_types:
        file_extension = file.name.lower().split('.')[-1]
        if file_extension not in allowed_types:
            return False, f"File type '{file_extension}' is not allowed"
    
    return True, "File is valid"