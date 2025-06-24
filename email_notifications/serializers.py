# email_notifications/serializers.py
# type: ignore

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import NewsletterSubscription, EmailNotification, EmailTemplate

User = get_user_model()

class NewsletterSubscriptionSerializer(serializers.ModelSerializer):
    """
    Serializer for newsletter subscriptions
    """
    user_name = serializers.SerializerMethodField()
    days_subscribed = serializers.SerializerMethodField()
    
    class Meta:
        model = NewsletterSubscription
        fields = [
            'id', 'email', 'user_name', 'is_active', 'is_verified',
            'content_uploads', 'live_videos', 'weekly_digest', 'monthly_newsletter',
            'subscribed_at', 'verified_at', 'subscription_source', 'days_subscribed'
        ]
        read_only_fields = ['id', 'subscribed_at', 'verified_at', 'user_name', 'days_subscribed']
    
    def get_user_name(self, obj):
        """Get user's full name if available"""
        if obj.user:
            return obj.user.get_full_name() or obj.user.username
        return None
    
    def get_days_subscribed(self, obj):
        """Get number of days since subscription"""
        from django.utils import timezone
        return (timezone.now() - obj.subscribed_at).days

class NewsletterSubscriptionCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating newsletter subscriptions
    """
    class Meta:
        model = NewsletterSubscription
        fields = ['email', 'content_uploads', 'live_videos', 'weekly_digest', 'monthly_newsletter']
        extra_kwargs = {
            'email': {'required': True},
        }
    
    def validate_email(self, value):
        """Validate email format"""
        return value.lower().strip()

class EmailNotificationSerializer(serializers.ModelSerializer):
    """
    Serializer for email notifications
    """
    recipient_name = serializers.SerializerMethodField()
    content_title = serializers.SerializerMethodField()
    time_since_sent = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailNotification
        fields = [
            'id', 'recipient_email', 'recipient_name', 'notification_type', 
            'subject', 'status', 'content_title', 'created_at', 'sent_at', 
            'opened_at', 'clicked_at', 'error_message', 'retry_count', 'time_since_sent'
        ]
        read_only_fields = ['id', 'created_at', 'sent_at', 'opened_at', 'clicked_at']
    
    def get_recipient_name(self, obj):
        """Get recipient's name if available"""
        if obj.recipient_user:
            return obj.recipient_user.get_full_name() or obj.recipient_user.username
        return None
    
    def get_content_title(self, obj):
        """Get related content title if available"""
        if obj.content_object:
            return getattr(obj.content_object, 'title', str(obj.content_object))
        return None
    
    def get_time_since_sent(self, obj):
        """Get time since email was sent"""
        if obj.sent_at:
            from django.utils import timezone
            delta = timezone.now() - obj.sent_at
            
            if delta.days > 0:
                return f"{delta.days} day{'s' if delta.days > 1 else ''} ago"
            elif delta.seconds > 3600:
                hours = delta.seconds // 3600
                return f"{hours} hour{'s' if hours > 1 else ''} ago"
            elif delta.seconds > 60:
                minutes = delta.seconds // 60
                return f"{minutes} minute{'s' if minutes > 1 else ''} ago"
            else:
                return "Just now"
        return None

class EmailTemplateSerializer(serializers.ModelSerializer):
    """
    Serializer for email templates
    """
    created_by_name = serializers.SerializerMethodField()
    variables_count = serializers.SerializerMethodField()
    
    class Meta:
        model = EmailTemplate
        fields = [
            'id', 'name', 'template_type', 'subject', 'html_content', 
            'text_content', 'variables', 'is_active', 'is_default',
            'created_at', 'updated_at', 'created_by_name', 'variables_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by_name', 'variables_count']
    
    def get_created_by_name(self, obj):
        """Get creator's name"""
        if obj.created_by:
            return obj.created_by.get_full_name() or obj.created_by.username
        return None
    
    def get_variables_count(self, obj):
        """Get count of template variables"""
        return len(obj.variables) if obj.variables else 0

class NewsletterPreferencesSerializer(serializers.Serializer):
    """
    Serializer for newsletter preferences update
    """
    subscribed = serializers.BooleanField(default=True)
    content_uploads = serializers.BooleanField(default=True)
    live_videos = serializers.BooleanField(default=True)
    weekly_digest = serializers.BooleanField(default=True)
    monthly_newsletter = serializers.BooleanField(default=True)

class NewsletterStatsSerializer(serializers.Serializer):
    """
    Serializer for newsletter statistics
    """
    total_subscriptions = serializers.IntegerField()
    active_subscriptions = serializers.IntegerField()
    verified_subscriptions = serializers.IntegerField()
    recent_subscriptions = serializers.IntegerField()
    subscription_sources = serializers.ListField()
    email_stats = serializers.DictField()

class EmailNotificationStatsSerializer(serializers.Serializer):
    """
    Serializer for email notification statistics
    """
    total_sent = serializers.IntegerField()
    total_failed = serializers.IntegerField()
    success_rate = serializers.FloatField()
    notifications_by_type = serializers.ListField()
    recent_notifications = EmailNotificationSerializer(many=True)

class NewsletterBlastSerializer(serializers.Serializer):
    """
    Serializer for sending newsletter blast
    """
    subject = serializers.CharField(max_length=200)
    content = serializers.CharField()
    newsletter_type = serializers.ChoiceField(
        choices=[
            ('custom', 'Custom'),
            ('weekly_digest', 'Weekly Digest'),
            ('monthly_newsletter', 'Monthly Newsletter'),
            ('content_upload', 'Content Upload'),
        ],
        default='custom'
    )
    send_to_all = serializers.BooleanField(default=True)
    test_email = serializers.EmailField(required=False)
    
    def validate_content(self, value):
        """Validate content is not empty"""
        if not value.strip():
            raise serializers.ValidationError("Content cannot be empty.")
        return value