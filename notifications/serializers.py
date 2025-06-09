# notifications/serializers.py - CREATE THIS FILE
# type: ignore

from rest_framework import serializers
from .models import Notification, NotificationSettings, NotificationTemplate

class NotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for notifications
    """
    
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    content_object_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'notification_type', 'title', 'message', 'priority',
            'is_read', 'is_clicked', 'action_url', 'created_at', 'read_at',
            'clicked_at', 'expires_at', 'sender_name', 'content_object_info'
        ]
        read_only_fields = ['id', 'created_at', 'read_at', 'clicked_at']
    
    def get_content_object_info(self, obj):
        """Get basic info about the related content object"""
        if obj.content_object:
            return {
                'type': obj.content_type.model,
                'title': getattr(obj.content_object, 'title', str(obj.content_object)),
                'id': str(obj.object_id) if obj.object_id else None
            }
        return None

class NotificationSettingsSerializer(serializers.ModelSerializer):
    """
    Serializer for notification settings
    """
    
    class Meta:
        model = NotificationSettings
        fields = [
            'email_notifications', 'push_notifications', 'sms_notifications',
            'in_app_notifications', 'content_likes', 'content_comments',
            'content_shares', 'new_content', 'new_followers', 'mentions',
            'system_alerts', 'admin_messages', 'recommendations',
            'email_frequency', 'quiet_hours_enabled', 'quiet_hours_start',
            'quiet_hours_end', 'marketing_notifications', 'digest_enabled'
        ]

class NotificationTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for notification templates
    """
    
    class Meta:
        model = NotificationTemplate
        fields = [
            'id', 'notification_type', 'title_template', 'message_template',
            'email_subject_template', 'email_body_template', 'push_title_template',
            'push_body_template', 'default_priority', 'default_delivery_methods',
            'default_expires_hours', 'available_variables', 'is_active'
        ]