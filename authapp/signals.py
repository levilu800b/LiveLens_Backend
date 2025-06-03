# type: ignore

from django.db.models.signals import post_save, pre_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
import os

User = get_user_model()

@receiver(post_save, sender=User)
def user_post_save(sender, instance, created, **kwargs):
    """Handle actions after user is saved"""
    if created:
        # Send welcome email after email verification
        if instance.is_verified:
            send_welcome_email(instance)

@receiver(pre_delete, sender=User)
def user_pre_delete(sender, instance, **kwargs):
    """Clean up user files before deletion"""
    # Delete avatar file if it exists
    if instance.avatar:
        if os.path.isfile(instance.avatar.path):
            os.remove(instance.avatar.path)

def send_welcome_email(user):
    """Send welcome email to newly verified users"""
    subject = 'Welcome to Streaming Platform!'
    
    html_message = f"""
    <html>
    <body>
        <h2>Welcome to Streaming Platform!</h2>
        <p>Hi {user.first_name},</p>
        <p>Welcome to our streaming platform! We're excited to have you on board.</p>
        <p>You now have access to all our exclusive content including:</p>
        <ul>
            <li>🎬 Films and Content</li>
            <li>📚 Stories</li>
            <li>🎙️ Podcasts</li>
            <li>🎥 Animations</li>
            <li>👀 Sneak Peeks</li>
        </ul>
        <p>Start exploring and enjoy your streaming experience!</p>
        <br>
        <p>Best regards,<br>Streaming Platform Team</p>
    </body>
    </html>
    """
    
    plain_message = f"""
    Welcome to Streaming Platform!
    
    Hi {user.first_name},
    
    Welcome to our streaming platform! We're excited to have you on board.
    
    You now have access to all our exclusive content including:
    - Films and Content
    - Stories
    - Podcasts
    - Animations
    - Sneak Peeks
    
    Start exploring and enjoy your streaming experience!
    
    Best regards,
    Streaming Platform Team
    """
    
    try:
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=True,
        )
    except Exception as e:
        # Log the error but don't raise it
        print(f"Failed to send welcome email to {user.email}: {e}")