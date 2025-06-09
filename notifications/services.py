# notifications/services.py
# type: ignore

from django.template import Template, Context
from django.utils import timezone
from django.core.mail import send_mail, EmailMultiAlternatives
from django.conf import settings
from datetime import timedelta
from typing import Dict, Any, List, Optional, Union
import logging
import json

from .models import (
    Notification, NotificationSettings, NotificationTemplate, 
    NotificationQueue
)
from authapp.models import User
from utils.email_service import email_service

logger = logging.getLogger(__name__)

class NotificationService:
    """
    Service for creating and managing notifications
    """
    
    def __init__(self):
        self.default_templates = self._load_default_templates()
    
    def create_notification(self, recipient: User, notification_type: str,
                          title: str = None, message: str = None,
                          sender: User = None, related_object: Any = None,
                          priority: str = 'normal',
                          delivery_methods: List[str] = None,
                          action_url: str = None,
                          action_data: Dict[str, Any] = None,
                          metadata: Dict[str, Any] = None,
                          template_variables: Dict[str, Any] = None,
                          scheduled_for: timezone.datetime = None,
                          expires_in_hours: int = None) -> Notification:
        """
        Create a new notification
        
        Args:
            recipient: User to receive the notification
            notification_type: Type of notification
            title: Notification title (optional if using template)
            message: Notification message (optional if using template)
            sender: User sending the notification (optional)
            related_object: Related content object (optional)
            priority: Priority level
            delivery_methods: List of delivery methods
            action_url: URL to redirect when clicked
            action_data: Additional action data
            metadata: Additional metadata
            template_variables: Variables for template rendering
            scheduled_for: When to deliver the notification
            expires_in_hours: Hours until notification expires
        
        Returns:
            Created notification instance
        """
        
        try:
            # Get user's notification settings
            settings_obj, _ = NotificationSettings.objects.get_or_create(user=recipient)
            
            # Check if user wants this type of notification
            if not self._should_send_notification(settings_obj, notification_type):
                logger.info(f"Skipping notification {notification_type} for user {recipient.id} due to settings")
                return None
            
            # Get template if exists
            template = self._get_template(notification_type)
            
            # Render content from template if available
            if template and not (title and message):
                rendered_content = self._render_template(template, template_variables or {})
                title = title or rendered_content['title']
                message = message or rendered_content['message']
                
                if not delivery_methods:
                    delivery_methods = template.default_delivery_methods
                if not expires_in_hours:
                    expires_in_hours = template.default_expires_hours
                if priority == 'normal':
                    priority = template.default_priority
            
            # Set defaults
            if not delivery_methods:
                delivery_methods = self._get_default_delivery_methods(settings_obj)
            
            if not expires_in_hours:
                expires_in_hours = 168  # 7 days
            
            # Create notification
            notification = Notification.objects.create(
                recipient=recipient,
                sender=sender,
                notification_type=notification_type,
                title=title or f"New {notification_type.replace('_', ' ').title()}",
                message=message or "You have a new notification",
                priority=priority,
                delivery_methods=delivery_methods,
                action_url=action_url or '',
                action_data=action_data or {},
                metadata=metadata or {},
                scheduled_for=scheduled_for,
                expires_at=timezone.now() + timedelta(hours=expires_in_hours),
                content_object=related_object
            )
            
            # Queue for delivery if not scheduled
            if not scheduled_for or scheduled_for <= timezone.now():
                self._queue_for_delivery(notification)
            
            logger.info(f"Created notification {notification.id} for user {recipient.id}")
            return notification
            
        except Exception as e:
            logger.error(f"Error creating notification: {e}")
            raise
    
    def send_bulk_notification(self, recipients: List[User], notification_type: str,
                             title: str, message: str, **kwargs) -> List[Notification]:
        """
        Send notification to multiple recipients
        
        Args:
            recipients: List of users to receive the notification
            notification_type: Type of notification
            title: Notification title
            message: Notification message
            **kwargs: Additional notification parameters
        
        Returns:
            List of created notifications
        """
        
        notifications = []
        for recipient in recipients:
            try:
                notification = self.create_notification(
                    recipient=recipient,
                    notification_type=notification_type,
                    title=title,
                    message=message,
                    **kwargs
                )
                if notification:
                    notifications.append(notification)
            except Exception as e:
                logger.warning(f"Failed to create notification for user {recipient.id}: {e}")
                continue
        
        logger.info(f"Created {len(notifications)} notifications for {len(recipients)} recipients")
        return notifications
    
    def mark_notification_as_read(self, notification_id: str, user: User) -> bool:
        """Mark notification as read"""
        
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=user
            )
            notification.mark_as_read()
            return True
            
        except Notification.DoesNotExist:
            logger.warning(f"Notification {notification_id} not found for user {user.id}")
            return False
        except Exception as e:
            logger.error(f"Error marking notification as read: {e}")
            return False
    
    def mark_notification_as_clicked(self, notification_id: str, user: User) -> bool:
        """Mark notification as clicked"""
        
        try:
            notification = Notification.objects.get(
                id=notification_id,
                recipient=user
            )
            notification.mark_as_clicked()
            return True
            
        except Notification.DoesNotExist:
            logger.warning(f"Notification {notification_id} not found for user {user.id}")
            return False
        except Exception as e:
            logger.error(f"Error marking notification as clicked: {e}")
            return False
    
    def get_user_notifications(self, user: User, limit: int = 20,
                             unread_only: bool = False,
                             notification_types: List[str] = None) -> List[Notification]:
        """Get notifications for a user"""
        
        try:
            queryset = Notification.objects.filter(recipient=user)
            
            if unread_only:
                queryset = queryset.filter(is_read=False)
            
            if notification_types:
                queryset = queryset.filter(notification_type__in=notification_types)
            
            # Exclude expired notifications
            queryset = queryset.exclude(
                expires_at__lt=timezone.now()
            )
            
            return list(queryset.order_by('-created_at')[:limit])
            
        except Exception as e:
            logger.error(f"Error getting user notifications: {e}")
            return []
    
    def get_unread_count(self, user: User) -> int:
        """Get count of unread notifications for a user"""
        
        try:
            return Notification.objects.filter(
                recipient=user,
                is_read=False,
                expires_at__gt=timezone.now()
            ).count()
            
        except Exception as e:
            logger.error(f"Error getting unread count: {e}")
            return 0
    
    def process_notification_queue(self, limit: int = 100) -> int:
        """Process pending notifications in the queue"""
        
        try:
            # Get pending queue items
            pending_items = NotificationQueue.objects.filter(
                status='pending'
            ).select_related('notification')[:limit]
            
            processed_count = 0
            
            for queue_item in pending_items:
                try:
                    # Check if it's time to process (for scheduled notifications)
                    notification = queue_item.notification
                    if notification.scheduled_for and notification.scheduled_for > timezone.now():
                        continue
                    
                    # Check if within quiet hours
                    if self._is_quiet_hours(notification.recipient):
                        continue
                    
                    # Process based on delivery method
                    success = self._deliver_notification(queue_item)
                    
                    if success:
                        queue_item.status = 'delivered'
                        queue_item.processed_at = timezone.now()
                        notification.mark_as_delivered()
                        processed_count += 1
                    else:
                        # Handle failure
                        queue_item.retry_count += 1
                        if queue_item.retry_count >= queue_item.max_retries:
                            queue_item.status = 'failed'
                        else:
                            queue_item.status = 'retry'
                            queue_item.next_retry_at = timezone.now() + timedelta(
                                minutes=5 * queue_item.retry_count  # Exponential backoff
                            )
                    
                    queue_item.save()
                    
                except Exception as e:
                    logger.error(f"Error processing queue item {queue_item.id}: {e}")
                    queue_item.status = 'failed'
                    queue_item.error_message = str(e)
                    queue_item.save()
                    continue
            
            logger.info(f"Processed {processed_count} notifications from queue")
            return processed_count
            
        except Exception as e:
            logger.error(f"Error processing notification queue: {e}")
            return 0
    
    def cleanup_old_notifications(self, days_old: int = 30) -> int:
        """Clean up old notifications"""
        
        try:
            cutoff_date = timezone.now() - timedelta(days=days_old)
            
            # Delete old read notifications
            deleted_count = Notification.objects.filter(
                is_read=True,
                created_at__lt=cutoff_date
            ).delete()[0]
            
            # Delete expired notifications
            expired_count = Notification.objects.filter(
                expires_at__lt=timezone.now()
            ).delete()[0]
            
            total_deleted = deleted_count + expired_count
            logger.info(f"Cleaned up {total_deleted} old notifications")
            return total_deleted
            
        except Exception as e:
            logger.error(f"Error cleaning up notifications: {e}")
            return 0
    
    def _should_send_notification(self, settings: NotificationSettings, 
                                notification_type: str) -> bool:
        """Check if user wants this type of notification"""
        
        if not settings.in_app_notifications:
            return False
        
        # Check specific notification type preferences
        type_mapping = {
            'content_like': settings.content_likes,
            'content_comment': settings.content_comments,
            'content_share': settings.content_shares,
            'new_content': settings.new_content,
            'new_follower': settings.new_followers,
            'mention': settings.mentions,
            'system_alert': settings.system_alerts,
            'admin_message': settings.admin_messages,
            'recommendation': settings.recommendations,
        }
        
        return type_mapping.get(notification_type, True)
    
    def _get_template(self, notification_type: str) -> Optional[NotificationTemplate]:
        """Get notification template"""
        
        try:
            return NotificationTemplate.objects.get(
                notification_type=notification_type,
                is_active=True
            )
        except NotificationTemplate.DoesNotExist:
            return None
    
    def _render_template(self, template: NotificationTemplate, 
                        variables: Dict[str, Any]) -> Dict[str, str]:
        """Render notification template"""
        
        try:
            context = Context(variables)
            
            title_template = Template(template.title_template)
            message_template = Template(template.message_template)
            
            return {
                'title': title_template.render(context),
                'message': message_template.render(context),
            }
            
        except Exception as e:
            logger.error(f"Error rendering template: {e}")
            return {
                'title': template.title_template,
                'message': template.message_template,
            }
    
    def _get_default_delivery_methods(self, settings: NotificationSettings) -> List[str]:
        """Get default delivery methods based on user settings"""
        
        methods = []
        
        if settings.in_app_notifications:
            methods.append('in_app')
        
        if settings.email_notifications and settings.email_frequency == 'immediate':
            methods.append('email')
        
        if settings.push_notifications:
            methods.append('push')
        
        if settings.sms_notifications:
            methods.append('sms')
        
        return methods or ['in_app']  # At least in-app
    
    def _queue_for_delivery(self, notification: Notification):
        """Queue notification for delivery"""
        
        for delivery_method in notification.delivery_methods:
            NotificationQueue.objects.create(
                notification=notification,
                delivery_method=delivery_method
            )
    
    def _is_quiet_hours(self, user: User) -> bool:
        """Check if current time is within user's quiet hours"""
        
        try:
            settings = user.notification_settings
            if not settings.quiet_hours_enabled:
                return False
            
            current_time = timezone.now().time()
            start_time = settings.quiet_hours_start
            end_time = settings.quiet_hours_end
            
            if not start_time or not end_time:
                return False
            
            # Handle quiet hours that span midnight
            if start_time <= end_time:
                return start_time <= current_time <= end_time
            else:
                return current_time >= start_time or current_time <= end_time
                
        except Exception as e:
            logger.warning(f"Error checking quiet hours: {e}")
            return False
    
    def _deliver_notification(self, queue_item: NotificationQueue) -> bool:
        """Deliver notification via specified method"""
        
        try:
            notification = queue_item.notification
            delivery_method = queue_item.delivery_method
            
            if delivery_method == 'in_app':
                # In-app notifications are already created, just mark as delivered
                return True
            
            elif delivery_method == 'email':
                return self._send_email_notification(notification)
            
            elif delivery_method == 'push':
                return self._send_push_notification(notification)
            
            elif delivery_method == 'sms':
                return self._send_sms_notification(notification)
            
            else:
                logger.warning(f"Unknown delivery method: {delivery_method}")
                return False
                
        except Exception as e:
            logger.error(f"Error delivering notification: {e}")
            queue_item.error_message = str(e)
            return False
    
    def _send_email_notification(self, notification: Notification) -> bool:
        """Send email notification"""
        
        try:
            recipient = notification.recipient
            
            # Use email service
            success = email_service.send_content_notification_email(
                user_email=recipient.email,
                user_name=recipient.full_name,
                content_title=notification.title,
                content_type='notification',
                content_url=notification.action_url or '#'
            )
            
            return success
            
        except Exception as e:
            logger.error(f"Error sending email notification: {e}")
            return False
    
    def _send_push_notification(self, notification: Notification) -> bool:
        """Send push notification"""
        
        try:
            # This would integrate with a push notification service
            # For now, we'll just log it
            logger.info(f"Would send push notification: {notification.title}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending push notification: {e}")
            return False
    
    def _send_sms_notification(self, notification: Notification) -> bool:
        """Send SMS notification"""
        
        try:
            # This would integrate with an SMS service
            # For now, we'll just log it
            logger.info(f"Would send SMS notification: {notification.title}")
            return True
            
        except Exception as e:
            logger.error(f"Error sending SMS notification: {e}")
            return False
    
    def _load_default_templates(self) -> Dict[str, Dict[str, str]]:
        """Load default notification templates"""
        
        return {
            'content_like': {
                'title': '{{ sender.full_name }} liked your {{ content_type }}',
                'message': '{{ sender.full_name }} liked your {{ content_type }} "{{ content_title }}"',
            },
            'content_comment': {
                'title': '{{ sender.full_name }} commented on your {{ content_type }}',
                'message': '{{ sender.full_name }} left a comment on "{{ content_title }}": {{ comment_text }}',
            },
            'new_content': {
                'title': 'New {{ content_type }} available!',
                'message': 'Check out the new {{ content_type }} "{{ content_title }}" by {{ author.full_name }}',
            },
            'system_alert': {
                'title': 'System Alert',
                'message': '{{ alert_message }}',
            },
        }

# Global notification service instance
notification_service = NotificationService()

# Convenience functions
def create_notification(recipient: User, notification_type: str, **kwargs) -> Notification:
    """Create a notification"""
    return notification_service.create_notification(recipient, notification_type, **kwargs)

def send_bulk_notification(recipients: List[User], notification_type: str, 
                          title: str, message: str, **kwargs) -> List[Notification]:
    """Send bulk notification"""
    return notification_service.send_bulk_notification(recipients, notification_type, title, message, **kwargs)

def mark_notification_read(notification_id: str, user: User) -> bool:
    """Mark notification as read"""
    return notification_service.mark_notification_as_read(notification_id, user)

def get_user_notifications(user: User, **kwargs) -> List[Notification]:
    """Get user notifications"""
    return notification_service.get_user_notifications(user, **kwargs)

def get_unread_notifications_count(user: User) -> int:
    """Get unread notifications count"""
    return notification_service.get_unread_count(user)