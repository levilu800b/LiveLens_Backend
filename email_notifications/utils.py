# email_notifications/utils.py
# type: ignore

from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.conf import settings
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from .models import EmailNotification, NewsletterSubscription
import logging
import uuid
import hashlib

logger = logging.getLogger(__name__)

def get_brand_colors():
    """Get consistent brand colors for email templates"""
    return {
        'primary': '#667eea',
        'secondary': '#764ba2',
        'success': '#10b981',
        'warning': '#f59e0b',
        'danger': '#ef4444',
        'dark': '#1f2937',
        'light': '#f9fafb',
    }

def get_base_email_style():
    """Get base CSS styles for all emails"""
    colors = get_brand_colors()
    return f"""
        <style>
            body {{
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f5f5f5;
            }}
            .email-container {{
                background: white;
                border-radius: 12px;
                overflow: hidden;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background: linear-gradient(135deg, {colors['primary']} 0%, {colors['secondary']} 100%);
                color: white;
                padding: 40px 30px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 700;
            }}
            .content {{
                padding: 40px 30px;
            }}
            .welcome-message {{
                font-size: 18px;
                margin-bottom: 20px;
                color: {colors['dark']};
            }}
            .button {{
                display: inline-block;
                background: linear-gradient(135deg, {colors['primary']} 0%, {colors['secondary']} 100%);
                color: white !important;
                text-decoration: none;
                padding: 15px 30px;
                border-radius: 8px;
                font-weight: 600;
                margin: 20px 0;
                transition: transform 0.2s ease;
            }}
            .button:hover {{
                transform: translateY(-2px);
            }}
            .info-box {{
                background: {colors['light']};
                border-left: 4px solid {colors['primary']};
                padding: 20px;
                margin: 20px 0;
                border-radius: 0 8px 8px 0;
            }}
            .footer {{
                background: {colors['dark']};
                color: #9ca3af;
                padding: 30px;
                text-align: center;
                font-size: 14px;
            }}
            .footer a {{
                color: {colors['primary']};
                text-decoration: none;
            }}
            .social-links {{
                margin: 20px 0;
            }}
            .social-links a {{
                display: inline-block;
                margin: 0 10px;
                padding: 10px;
                background: {colors['primary']};
                color: white;
                border-radius: 50%;
                text-decoration: none;
                width: 40px;
                height: 40px;
                line-height: 20px;
                text-align: center;
            }}
            .divider {{
                height: 1px;
                background: #e5e7eb;
                margin: 30px 0;
            }}
            .content-preview {{
                border: 1px solid #e5e7eb;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                background: #fafafa;
            }}
            .content-preview h3 {{
                margin-top: 0;
                color: {colors['primary']};
            }}
            .live-badge {{
                background: {colors['danger']};
                color: white;
                padding: 4px 12px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: 600;
                text-transform: uppercase;
                display: inline-block;
                margin-bottom: 10px;
            }}
        </style>
    """

def send_welcome_email(user):
    """
    Send welcome email to newly registered user
    """
    try:
        subject = f'Welcome to LiveLens - Your Journey Begins Now! 🎬'
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Welcome to LiveLens</title>
            {get_base_email_style()}
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>🎬 Welcome to LiveLens!</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">
                        Your gateway to amazing stories and content
                    </p>
                </div>
                
                <div class="content">
                    <div class="welcome-message">
                        <strong>Hi {user.first_name},</strong>
                    </div>
                    
                    <p>🎉 <strong>Congratulations!</strong> Your account has been successfully created and verified. You're now part of the LiveLens community!</p>
                    
                    <div class="info-box">
                        <h3 style="margin-top: 0;">🚀 What's Next?</h3>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li><strong>Explore Stories</strong> - Dive into captivating written content</li>
                            <li><strong>Watch Films</strong> - Enjoy our curated film collection</li>
                            <li><strong>Listen to Podcasts</strong> - Discover engaging audio content</li>
                            <li><strong>View Animations</strong> - Experience creative visual storytelling</li>
                            <li><strong>Catch Sneak Peeks</strong> - Get early access to upcoming content</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{settings.FRONTEND_URL}" class="button">
                            🎬 Start Exploring Now
                        </a>
                    </div>
                    
                    <div class="divider"></div>
                    
                    <h3>💡 Pro Tips:</h3>
                    <ul>
                        <li>Like content to add it to your favorites</li>
                        <li>Check your library to track your progress</li>
                        <li>Enable notifications to never miss new uploads</li>
                        <li>Subscribe to our newsletter for weekly updates</li>
                    </ul>
                    
                    <p>If you have any questions or need help getting started, don't hesitate to reach out to our support team.</p>
                    
                    <p style="margin-top: 30px;">
                        <strong>Welcome aboard!</strong><br>
                        The LiveLens Team 🎭
                    </p>
                </div>
                
                <div class="footer">
                    <div class="social-links">
                        <a href="#" title="Instagram">📷</a>
                        <a href="#" title="Twitter">🐦</a>
                        <a href="#" title="YouTube">🎥</a>
                    </div>
                    <p>
                        © 2025 LiveLens. Made with ❤️ in San Francisco<br>
                        <a href="{settings.FRONTEND_URL}/unsubscribe">Unsubscribe</a> | 
                        <a href="{settings.FRONTEND_URL}/privacy">Privacy Policy</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
        Hi {user.first_name},
        
        🎉 Congratulations! Your LiveLens account has been successfully created and verified.
        
        You're now part of our community and can:
        • Explore captivating stories
        • Watch curated films
        • Listen to engaging podcasts
        • View creative animations
        • Get early access to sneak peeks
        
        Start exploring: {settings.FRONTEND_URL}
        
        Welcome aboard!
        The LiveLens Team
        
        ---
        This is an automated message. Please do not reply to this email.
        """
        
        # Create email notification record
        notification = EmailNotification.objects.create(
            recipient_email=user.email,
            recipient_user=user,
            notification_type='welcome',
            subject=subject
        )
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        notification.mark_as_sent()
        logger.info(f"Welcome email sent successfully to {user.email}")
        
    except Exception as e:
        logger.error(f"Failed to send welcome email to {user.email}: {str(e)}")
        if 'notification' in locals():
            notification.mark_as_failed(str(e))

def send_password_changed_email(user, ip_address=None):
    """
    Send password change confirmation email
    """
    try:
        subject = '🔒 Password Changed Successfully - LiveLens'
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Password Changed</title>
            {get_base_email_style()}
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>🔒 Password Changed</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">
                        Your account security has been updated
                    </p>
                </div>
                
                <div class="content">
                    <div class="welcome-message">
                        <strong>Hi {user.first_name},</strong>
                    </div>
                    
                    <p>✅ Your password has been successfully changed on your LiveLens account.</p>
                    
                    <div class="info-box">
                        <h3 style="margin-top: 0;">🛡️ Security Details</h3>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li><strong>Account:</strong> {user.email}</li>
                            <li><strong>Changed:</strong> {timezone.now().strftime('%B %d, %Y at %I:%M %p')}</li>
                            {'<li><strong>IP Address:</strong> ' + ip_address + '</li>' if ip_address else ''}
                        </ul>
                    </div>
                    
                    <div style="background: #fef3f2; border: 1px solid #fecaca; border-radius: 8px; padding: 20px; margin: 20px 0;">
                        <h3 style="margin-top: 0; color: #dc2626;">🚨 Didn't change your password?</h3>
                        <p style="margin-bottom: 0;">If you didn't make this change, please contact our support team immediately and consider changing your password again.</p>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{settings.FRONTEND_URL}/profile" class="button">
                            👤 Manage Account
                        </a>
                    </div>
                    
                    <p>For your security, we recommend:</p>
                    <ul>
                        <li>Using a strong, unique password</li>
                        <li>Enabling two-factor authentication (coming soon)</li>
                        <li>Regularly reviewing your account activity</li>
                    </ul>
                    
                    <p style="margin-top: 30px;">
                        <strong>Stay secure!</strong><br>
                        The LiveLens Security Team 🛡️
                    </p>
                </div>
                
                <div class="footer">
                    <p>
                        © 2025 LiveLens. Made with ❤️ in San Francisco<br>
                        <a href="mailto:security@livelens.com">Report Security Issue</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
        Hi {user.first_name},
        
        ✅ Your password has been successfully changed on your LiveLens account.
        
        Security Details:
        • Account: {user.email}
        • Changed: {timezone.now().strftime('%B %d, %Y at %I:%M %p')}
        {'• IP Address: ' + ip_address if ip_address else ''}
        
        🚨 If you didn't make this change, please contact our support team immediately.
        
        Manage your account: {settings.FRONTEND_URL}/profile
        
        Stay secure!
        The LiveLens Security Team
        
        ---
        This is an automated security notification.
        """
        
        # Create email notification record
        notification = EmailNotification.objects.create(
            recipient_email=user.email,
            recipient_user=user,
            notification_type='password_changed',
            subject=subject
        )
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=False,
        )
        
        notification.mark_as_sent()
        logger.info(f"Password changed email sent successfully to {user.email}")
        
    except Exception as e:
        logger.error(f"Failed to send password changed email to {user.email}: {str(e)}")
        if 'notification' in locals():
            notification.mark_as_failed(str(e))

def send_newsletter_confirmation_email(email, verification_token):
    """
    Send newsletter subscription confirmation email
    """
    try:
        subject = '📧 Confirm Your Newsletter Subscription - LiveLens'
        verification_url = f"{settings.FRONTEND_URL}/newsletter/verify/{verification_token}"
        
        html_message = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Confirm Newsletter Subscription</title>
            {get_base_email_style()}
        </head>
        <body>
            <div class="email-container">
                <div class="header">
                    <h1>📧 Almost There!</h1>
                    <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">
                        Confirm your newsletter subscription
                    </p>
                </div>
                
                <div class="content">
                    <div class="welcome-message">
                        <strong>Hi there!</strong>
                    </div>
                    
                    <p>🎉 Thank you for subscribing to the LiveLens newsletter! You're just one click away from staying updated with our latest content.</p>
                    
                    <div class="info-box">
                        <h3 style="margin-top: 0;">📬 What You'll Receive:</h3>
                        <ul style="margin: 0; padding-left: 20px;">
                            <li><strong>New Content Alerts</strong> - Be first to know about new stories, films, and podcasts</li>
                            <li><strong>Live Stream Notifications</strong> - Never miss when we go live</li>
                            <li><strong>Weekly Digest</strong> - Curated highlights from the past week</li>
                            <li><strong>Exclusive Updates</strong> - Behind-the-scenes content and announcements</li>
                        </ul>
                    </div>
                    
                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{verification_url}" class="button">
                            ✅ Confirm Subscription
                        </a>
                    </div>
                    
                    <p style="font-size: 14px; color: #6b7280;">
                        Can't click the button? Copy and paste this link into your browser:<br>
                        <a href="{verification_url}" style="color: #667eea; word-break: break-all;">{verification_url}</a>
                    </p>
                    
                    <div class="divider"></div>
                    
                    <p style="font-size: 14px; color: #6b7280;">
                        If you didn't subscribe to our newsletter, you can safely ignore this email.
                    </p>
                    
                    <p style="margin-top: 30px;">
                        <strong>Looking forward to sharing great content with you!</strong><br>
                        The LiveLens Team 📺
                    </p>
                </div>
                
                <div class="footer">
                    <p>
                        © 2025 LiveLens. Made with ❤️ in San Francisco<br>
                        <a href="{settings.FRONTEND_URL}/privacy">Privacy Policy</a>
                    </p>
                </div>
            </div>
        </body>
        </html>
        """
        
        plain_message = f"""
        Hi there!
        
        🎉 Thank you for subscribing to the LiveLens newsletter!
        
        Please confirm your subscription by clicking this link:
        {verification_url}
        
        What you'll receive:
        • New content alerts
        • Live stream notifications  
        • Weekly digest
        • Exclusive updates
        
        If you didn't subscribe, you can safely ignore this email.
        
        Looking forward to sharing great content with you!
        The LiveLens Team
        
        ---
        © 2025 LiveLens. Privacy Policy: {settings.FRONTEND_URL}/privacy
        """
        
        # Create email notification record
        notification = EmailNotification.objects.create(
            recipient_email=email,
            notification_type='newsletter_confirmation',
            subject=subject
        )
        
        # Send email
        send_mail(
            subject=subject,
            message=plain_message,
            html_message=html_message,
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[email],
            fail_silently=False,
        )
        
        notification.mark_as_sent()
        logger.info(f"Newsletter confirmation email sent successfully to {email}")
        
    except Exception as e:
        logger.error(f"Failed to send newsletter confirmation email to {email}: {str(e)}")
        if 'notification' in locals():
            notification.mark_as_failed(str(e))

def send_content_upload_notification(content_instance, content_type_name):
    """
    Send notification to newsletter subscribers about new content upload
    """
    try:
        # Get all active newsletter subscribers who want content notifications
        subscribers = NewsletterSubscription.objects.filter(
            is_active=True,
            is_verified=True,
            content_uploads=True
        )
        
        if not subscribers.exists():
            return
        
        # Determine content type emoji and display name
        content_emojis = {
            'story': '📖',
            'film': '🎬',
            'content': '🎥',
            'podcast': '🎧',
            'animation': '🎨',
            'sneak_peek': '👀'
        }
        
        emoji = content_emojis.get(content_type_name, '🎯')
        display_name = content_type_name.replace('_', ' ').title()
        
        subject = f'{emoji} New {display_name}: {content_instance.title} - LiveLens'
        
        # Get content URL
        content_url = f"{settings.FRONTEND_URL}/{content_type_name}s/{content_instance.slug}"
        
        for subscriber in subscribers:
            try:
                html_message = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>New Content Available</title>
                    {get_base_email_style()}
                </head>
                <body>
                    <div class="email-container">
                        <div class="header">
                            <h1>{emoji} New {display_name} Available!</h1>
                            <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">
                                Fresh content just for you
                            </p>
                        </div>
                        
                        <div class="content">
                            <div class="welcome-message">
                                <strong>Hi {'there' if not subscriber.user else subscriber.user.first_name}!</strong>
                            </div>
                            
                            <p>🎉 We've just uploaded new content that we think you'll love!</p>
                            
                            <div class="content-preview">
                                <h3>{content_instance.title}</h3>
                                <p>{getattr(content_instance, 'short_description', getattr(content_instance, 'description', ''))[:200]}...</p>
                                
                                <div style="margin: 15px 0;">
                                    {'<strong>Author:</strong> ' + content_instance.author.get_full_name() if hasattr(content_instance, 'author') else ''}
                                    {'<strong>Creator:</strong> ' + content_instance.creator.get_full_name() if hasattr(content_instance, 'creator') else ''}
                                    {'<br><strong>Duration:</strong> ' + str(content_instance.duration) + ' minutes' if hasattr(content_instance, 'duration') and content_instance.duration else ''}
                                    {'<br><strong>Category:</strong> ' + content_instance.category.replace('_', ' ').title() if hasattr(content_instance, 'category') else ''}
                                </div>
                            </div>
                            
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{content_url}" class="button">
                                    {emoji} View Now
                                </a>
                            </div>
                            
                            <p style="margin-top: 30px;">
                                <strong>Happy viewing!</strong><br>
                                The LiveLens Team 🎭
                            </p>
                        </div>
                        
                        <div class="footer">
                            <p>
                                © 2025 LiveLens. Made with ❤️ in San Francisco<br>
                                <a href="{settings.FRONTEND_URL}/newsletter/unsubscribe/{subscriber.id}">Unsubscribe</a> | 
                                <a href="{settings.FRONTEND_URL}/privacy">Privacy Policy</a>
                            </p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                plain_message = f"""
                Hi {'there' if not subscriber.user else subscriber.user.first_name}!
                
                🎉 New {display_name} Available: {content_instance.title}
                
                {getattr(content_instance, 'short_description', getattr(content_instance, 'description', ''))[:300]}
                
                View now: {content_url}
                
                Happy viewing!
                The LiveLens Team
                
                ---
                Unsubscribe: {settings.FRONTEND_URL}/newsletter/unsubscribe/{subscriber.id}
                """
                
                # Create email notification record
                notification = EmailNotification.objects.create(
                    recipient_email=subscriber.email,
                    recipient_user=subscriber.user,
                    notification_type='content_upload',
                    subject=subject,
                    content_type=ContentType.objects.get_for_model(content_instance),
                    object_id=content_instance.id
                )
                
                # Send email
                send_mail(
                    subject=subject,
                    message=plain_message,
                    html_message=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[subscriber.email],
                    fail_silently=False,
                )
                
                notification.mark_as_sent()
                
            except Exception as e:
                logger.error(f"Failed to send content notification to {subscriber.email}: {str(e)}")
                if 'notification' in locals():
                    notification.mark_as_failed(str(e))
        
        logger.info(f"Content upload notifications sent for {content_instance.title} to {subscribers.count()} subscribers")
        
    except Exception as e:
        logger.error(f"Failed to send content upload notifications: {str(e)}")

def send_live_video_notification():
    """
    Send notification to subscribers when going live
    """
    try:
        # Get all active newsletter subscribers who want live notifications
        subscribers = NewsletterSubscription.objects.filter(
            is_active=True,
            is_verified=True,
            live_videos=True
        )
        
        if not subscribers.exists():
            return
        
        subject = '🔴 LIVE NOW - Join Us on LiveLens!'
        live_url = f"{settings.FRONTEND_URL}/live"
        
        for subscriber in subscribers:
            try:
                html_message = f"""
                <!DOCTYPE html>
                <html>
                <head>
                    <meta charset="utf-8">
                    <title>We're Live Now!</title>
                    {get_base_email_style()}
                </head>
                <body>
                    <div class="email-container">
                        <div class="header">
                            <h1>🔴 We're LIVE Now!</h1>
                            <div class="live-badge">● LIVE</div>
                            <p style="margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">
                                Don't miss out - join us right now!
                            </p>
                        </div>
                        
                        <div class="content">
                            <div class="welcome-message">
                                <strong>Hi {'there' if not subscriber.user else subscriber.user.first_name}!</strong>
                            </div>
                            
                            <p>🚀 <strong>We're going live right now!</strong> Join us for an exciting live session with fresh content, behind-the-scenes moments, and real-time interaction.</p>
                            
                            <div class="info-box">
                                <h3 style="margin-top: 0;">🎬 What's Happening Live:</h3>
                                <ul style="margin: 0; padding-left: 20px;">
                                    <li>Exclusive content previews</li>
                                    <li>Live Q&A session</li>
                                    <li>Behind-the-scenes insights</li>
                                    <li>Real-time audience interaction</li>
                                    <li>Special announcements</li>
                                </ul>
                            </div>
                            
                            <div style="text-align: center; margin: 30px 0;">
                                <a href="{live_url}" class="button">
                                    🔴 Join Live Stream
                                </a>
                            </div>
                            
                            <div style="background: #fef3f2; border: 1px solid #fecaca; border-radius: 8px; padding: 20px; margin: 20px 0;">
                                <h3 style="margin-top: 0; color: #dc2626;">⏰ Don't Wait!</h3>
                                <p style="margin-bottom: 0;">Live streams are time-sensitive. Join now to catch all the action from the beginning!</p>
                            </div>
                            
                            <p style="margin-top: 30px;">
                                <strong>See you live!</strong><br>
                                The LiveLens Team 🎭
                            </p>
                        </div>
                        
                        <div class="footer">
                            <div class="social-links">
                                <a href="#" title="Instagram">📷</a>
                                <a href="#" title="Twitter">🐦</a>
                                <a href="#" title="YouTube">🎥</a>
                            </div>
                            <p>
                                © 2025 LiveLens. Made with ❤️ in San Francisco<br>
                                <a href="{settings.FRONTEND_URL}/newsletter/unsubscribe/{subscriber.id}">Unsubscribe</a> | 
                                <a href="{settings.FRONTEND_URL}/privacy">Privacy Policy</a>
                            </p>
                        </div>
                    </div>
                </body>
                </html>
                """
                
                plain_message = f"""
                Hi {'there' if not subscriber.user else subscriber.user.first_name}!
                
                🔴 WE'RE LIVE NOW!
                
                Join us for an exciting live session with:
                • Exclusive content previews
                • Live Q&A session  
                • Behind-the-scenes insights
                • Real-time audience interaction
                • Special announcements
                
                ⏰ Don't wait - join now!
                {live_url}
                
                See you live!
                The LiveLens Team
                
                ---
                Unsubscribe: {settings.FRONTEND_URL}/newsletter/unsubscribe/{subscriber.id}
                """
                
                # Create email notification record
                notification = EmailNotification.objects.create(
                    recipient_email=subscriber.email,
                    recipient_user=subscriber.user,
                    notification_type='live_video',
                    subject=subject
                )
                
                # Send email
                send_mail(
                    subject=subject,
                    message=plain_message,
                    html_message=html_message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[subscriber.email],
                    fail_silently=False,
                )
                
                notification.mark_as_sent()
                
            except Exception as e:
                logger.error(f"Failed to send live notification to {subscriber.email}: {str(e)}")
                if 'notification' in locals():
                    notification.mark_as_failed(str(e))
        
        logger.info(f"Live video notifications sent to {subscribers.count()} subscribers")
        
    except Exception as e:
        logger.error(f"Failed to send live video notifications: {str(e)}")

def generate_newsletter_token(email):
    """Generate unique verification token for newsletter subscription"""
    timestamp = str(timezone.now().timestamp())
    return hashlib.sha256(f"{email}{timestamp}{settings.SECRET_KEY}".encode()).hexdigest()[:32]