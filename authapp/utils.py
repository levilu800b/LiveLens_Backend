# type: ignore
# authapp/utils.py


from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from django.utils.html import strip_tags


def send_verification_email(email, code):
    """Send email verification code to user"""
    subject = 'Verify Your Email - Streaming Platform'
    
    html_message = render_to_string('emails/verification_email.html', {
        'code': code,
        'email': email,
    })
    
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending verification email: {e}")
        return False


def send_password_reset_email(email, code):
    """Send password reset code to user"""
    subject = 'Reset Your Password - Streaming Platform'
    
    html_message = render_to_string('emails/password_reset_email.html', {
        'code': code,
        'email': email,
    })
    
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending password reset email: {e}")
        return False


def send_welcome_email(user):
    """Send welcome email to newly verified user"""
    subject = 'Welcome to Streaming Platform!'
    
    html_message = render_to_string('emails/welcome_email.html', {
        'user': user,
    })
    
    plain_message = strip_tags(html_message)
    
    try:
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return True
    except Exception as e:
        print(f"Error sending welcome email: {e}")
        return False