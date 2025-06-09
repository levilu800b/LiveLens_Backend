# utils/email_service.py
# type: ignore

from django.core.mail import send_mail, EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from typing import Optional, Dict, Any, List
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """
    Centralized email service for the streaming platform
    """
    
    def __init__(self):
        self.from_email = settings.DEFAULT_FROM_EMAIL
        self.platform_name = "StreamVault"  # Your platform name
        self.platform_url = "https://streamvault.com"  # Your platform URL
    
    def send_verification_email(self, user_email: str, verification_code: str, user_name: str = "") -> bool:
        """Send email verification code"""
        
        context = {
            'verification_code': verification_code,
            'user_name': user_name or 'User',
            'platform_name': self.platform_name,
            'platform_url': self.platform_url
        }
        
        subject = f"Verify Your {self.platform_name} Account"
        
        html_content = self._render_email_template('verification_email.html', context)
        text_content = f"""
        Hi {user_name or 'there'},
        
        Welcome to {self.platform_name}! Please verify your account using this code:
        
        {verification_code}
        
        Enter this code on the verification page to complete your registration.
        
        If you didn't create an account, please ignore this email.
        
        Best regards,
        The {self.platform_name} Team
        """
        
        return self._send_email(user_email, subject, text_content, html_content)
    
    def send_password_reset_email(self, user_email: str, reset_code: str, user_name: str = "") -> bool:
        """Send password reset code"""
        
        context = {
            'reset_code': reset_code,
            'user_name': user_name or 'User',
            'platform_name': self.platform_name,
            'platform_url': self.platform_url
        }
        
        subject = f"Reset Your {self.platform_name} Password"
        
        html_content = self._render_email_template('password_reset_email.html', context)
        text_content = f"""
        Hi {user_name or 'there'},
        
        You requested to reset your password for {self.platform_name}.
        
        Use this verification code: {reset_code}
        
        If you didn't request this reset, please ignore this email.
        
        Best regards,
        The {self.platform_name} Team
        """
        
        return self._send_email(user_email, subject, text_content, html_content)
    
    def send_welcome_email(self, user_email: str, user_name: str) -> bool:
        """Send welcome email after successful verification"""
        
        context = {
            'user_name': user_name,
            'platform_name': self.platform_name,
            'platform_url': self.platform_url,
            'dashboard_url': f"{self.platform_url}/dashboard",
            'explore_url': f"{self.platform_url}/explore"
        }
        
        subject = f"Welcome to {self.platform_name}! 🎉"
        
        html_content = self._render_email_template('welcome_email.html', context)
        text_content = f"""
        Hi {user_name},
        
        Welcome to {self.platform_name}! 🎉
        
        Your account has been successfully verified. You can now:
        
        • Explore our vast library of stories, films, and animations
        • Stream unlimited content
        • Create your own playlists and favorites
        • Leave comments and engage with the community
        
        Start exploring: {self.platform_url}/explore
        
        Thank you for joining us!
        
        Best regards,
        The {self.platform_name} Team
        """
        
        return self._send_email(user_email, subject, text_content, html_content)
    
    def send_content_notification_email(self, user_email: str, user_name: str, content_title: str, content_type: str, content_url: str) -> bool:
        """Send notification about new content"""
        
        context = {
            'user_name': user_name,
            'content_title': content_title,
            'content_type': content_type,
            'content_url': content_url,
            'platform_name': self.platform_name,
            'platform_url': self.platform_url
        }
        
        subject = f"New {content_type.title()}: {content_title}"
        
        html_content = self._render_email_template('content_notification_email.html', context)
        text_content = f"""
        Hi {user_name},
        
        Great news! A new {content_type} is now available on {self.platform_name}:
        
        "{content_title}"
        
        Watch it now: {content_url}
        
        Don't miss out on the latest content!
        
        Best regards,
        The {self.platform_name} Team
        """
        
        return self._send_email(user_email, subject, text_content, html_content)
    
    def send_comment_notification_email(self, user_email: str, user_name: str, commenter_name: str, content_title: str, comment_text: str, content_url: str) -> bool:
        """Send notification about new comment on user's content"""
        
        context = {
            'user_name': user_name,
            'commenter_name': commenter_name,
            'content_title': content_title,
            'comment_text': comment_text[:200] + ('...' if len(comment_text) > 200 else ''),
            'content_url': content_url,
            'platform_name': self.platform_name
        }
        
        subject = f"New comment on {content_title}"
        
        html_content = self._render_email_template('comment_notification_email.html', context)
        text_content = f"""
        Hi {user_name},
        
        {commenter_name} left a comment on "{content_title}":
        
        "{comment_text[:200]}{'...' if len(comment_text) > 200 else ''}"
        
        View and reply: {content_url}
        
        Best regards,
        The {self.platform_name} Team
        """
        
        return self._send_email(user_email, subject, text_content, html_content)
    
    def send_admin_alert_email(self, admin_emails: List[str], alert_title: str, alert_description: str, alert_priority: str) -> bool:
        """Send alert notification to admins"""
        
        context = {
            'alert_title': alert_title,
            'alert_description': alert_description,
            'alert_priority': alert_priority,
            'platform_name': self.platform_name,
            'admin_dashboard_url': f"{self.platform_url}/admin/dashboard"
        }
        
        subject = f"🚨 {alert_priority.upper()} Alert: {alert_title}"
        
        html_content = self._render_email_template('admin_alert_email.html', context)
        text_content = f"""
        ADMIN ALERT - {alert_priority.upper()} PRIORITY
        
        {alert_title}
        
        Description: {alert_description}
        
        Please check the admin dashboard for more details: {self.platform_url}/admin/dashboard
        
        {self.platform_name} Admin System
        """
        
        return self._send_bulk_email(admin_emails, subject, text_content, html_content)
    
    def send_account_deletion_confirmation_email(self, user_email: str, user_name: str) -> bool:
        """Send confirmation email for account deletion"""
        
        context = {
            'user_name': user_name,
            'platform_name': self.platform_name,
            'support_email': 'support@streamvault.com'
        }
        
        subject = f"Account Deletion Confirmation - {self.platform_name}"
        
        html_content = self._render_email_template('account_deletion_email.html', context)
        text_content = f"""
        Hi {user_name},
        
        Your {self.platform_name} account has been successfully deleted.
        
        We're sorry to see you go! If you have any feedback or concerns, please don't hesitate to reach out to us.
        
        Thank you for being part of our community.
        
        Best regards,
        The {self.platform_name} Team
        """
        
        return self._send_email(user_email, subject, text_content, html_content)
    
    def _render_email_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render HTML email template"""
        
        try:
            # Add common context variables
            context.update({
                'current_year': 2025,
                'platform_name': self.platform_name,
                'platform_url': self.platform_url,
                'unsubscribe_url': f"{self.platform_url}/unsubscribe",
                'privacy_url': f"{self.platform_url}/privacy",
                'support_email': 'support@streamvault.com'
            })
            
            return render_to_string(f'emails/{template_name}', context)
        except Exception as e:
            logger.error(f"Error rendering email template {template_name}: {e}")
            return self._get_fallback_html_template(context)
    
    def _get_fallback_html_template(self, context: Dict[str, Any]) -> str:
        """Fallback HTML template when main template fails"""
        
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>{context.get('subject', self.platform_name)}</title>
        </head>
        <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px;">
            <div style="text-align: center; margin-bottom: 30px;">
                <h1 style="color: #333;">{self.platform_name}</h1>
            </div>
            
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px;">
                <p>Hi {context.get('user_name', 'there')},</p>
                <p>{context.get('message', 'Thank you for using our platform!')}</p>
            </div>
            
            <div style="text-align: center; margin-top: 30px; font-size: 12px; color: #666;">
                <p>&copy; 2025 {self.platform_name}. All rights reserved.</p>
            </div>
        </body>
        </html>
        """
    
    def _send_email(self, recipient_email: str, subject: str, text_content: str, html_content: str = None) -> bool:
        """Send individual email"""
        
        try:
            if html_content:
                email = EmailMultiAlternatives(
                    subject=subject,
                    body=text_content,
                    from_email=self.from_email,
                    to=[recipient_email]
                )
                email.attach_alternative(html_content, "text/html")
                email.send()
            else:
                send_mail(
                    subject=subject,
                    message=text_content,
                    from_email=self.from_email,
                    recipient_list=[recipient_email],
                    fail_silently=False
                )
            
            logger.info(f"Email sent successfully to {recipient_email}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to send email to {recipient_email}: {e}")
            return False
    
    def _send_bulk_email(self, recipient_emails: List[str], subject: str, text_content: str, html_content: str = None) -> bool:
        """Send bulk email to multiple recipients"""
        
        success_count = 0
        for email in recipient_emails:
            if self._send_email(email, subject, text_content, html_content):
                success_count += 1
        
        logger.info(f"Bulk email sent to {success_count}/{len(recipient_emails)} recipients")
        return success_count > 0

# Global email service instance
email_service = EmailService()

# Convenience functions
def send_verification_email(user_email: str, verification_code: str, user_name: str = "") -> bool:
    """Send verification email"""
    return email_service.send_verification_email(user_email, verification_code, user_name)

def send_password_reset_email(user_email: str, reset_code: str, user_name: str = "") -> bool:
    """Send password reset email"""
    return email_service.send_password_reset_email(user_email, reset_code, user_name)

def send_welcome_email(user_email: str, user_name: str) -> bool:
    """Send welcome email"""
    return email_service.send_welcome_email(user_email, user_name)

def send_content_notification_email(user_email: str, user_name: str, content_title: str, content_type: str, content_url: str) -> bool:
    """Send content notification email"""
    return email_service.send_content_notification_email(user_email, user_name, content_title, content_type, content_url)

def send_comment_notification_email(user_email: str, user_name: str, commenter_name: str, content_title: str, comment_text: str, content_url: str) -> bool:
    """Send comment notification email"""
    return email_service.send_comment_notification_email(user_email, user_name, commenter_name, content_title, comment_text, content_url)

def send_admin_alert_email(admin_emails: List[str], alert_title: str, alert_description: str, alert_priority: str) -> bool:
    """Send admin alert email"""
    return email_service.send_admin_alert_email(admin_emails, alert_title, alert_description, alert_priority)

def send_account_deletion_confirmation_email(user_email: str, user_name: str) -> bool:
    """Send account deletion confirmation email"""
    return email_service.send_account_deletion_confirmation_email(user_email, user_name)