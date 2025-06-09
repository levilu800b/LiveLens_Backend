# admin_dashboard/serializers.py
# type: ignore

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Count, Sum, Avg
from .models import DashboardStats, ContentAnalytics, UserActivity, SystemAlert, ReportGeneration

User = get_user_model()

class DashboardStatsSerializer(serializers.ModelSerializer):
    """Serializer for dashboard statistics"""
    
    metric_type_display = serializers.CharField(source='get_metric_type_display', read_only=True)
    stat_type_display = serializers.CharField(source='get_stat_type_display', read_only=True)
    
    class Meta:
        model = DashboardStats
        fields = [
            'id', 'metric_type', 'metric_type_display', 'stat_type', 
            'stat_type_display', 'value', 'percentage_change', 'date',
            'period_start', 'period_end', 'metadata'
        ]


class ContentAnalyticsSerializer(serializers.ModelSerializer):
    """Serializer for content analytics"""
    
    engagement_rate = serializers.SerializerMethodField()
    avg_rating = serializers.SerializerMethodField()
    
    class Meta:
        model = ContentAnalytics
        fields = [
            'id', 'content_type', 'content_id', 'content_title',
            'views_count', 'unique_views_count', 'likes_count', 'dislikes_count',
            'comments_count', 'shares_count', 'downloads_count',
            'average_watch_time', 'completion_rate', 'bounce_rate',
            'return_viewer_rate', 'top_countries', 'age_demographics',
            'device_breakdown', 'traffic_sources', 'hourly_views',
            'daily_views', 'weekly_views', 'performance_score',
            'trending_score', 'engagement_rate', 'avg_rating', 'date'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_engagement_rate(self, obj):
        """Calculate engagement rate"""
        if obj.views_count == 0:
            return 0.0
        
        total_engagements = obj.likes_count + obj.comments_count + obj.shares_count
        return round((total_engagements / obj.views_count) * 100, 2)
    
    def get_avg_rating(self, obj):
        """Calculate average rating if available"""
        if obj.likes_count + obj.dislikes_count == 0:
            return 0.0
        
        return round((obj.likes_count / (obj.likes_count + obj.dislikes_count)) * 5, 2)


class UserActivitySerializer(serializers.ModelSerializer):
    """Serializer for user activities"""
    
    user_display = serializers.SerializerMethodField()
    activity_type_display = serializers.CharField(source='get_activity_type_display', read_only=True)
    content_title = serializers.SerializerMethodField()
    
    class Meta:
        model = UserActivity
        fields = [
            'id', 'user', 'user_display', 'activity_type', 'activity_type_display',
            'description', 'content_title', 'ip_address', 'device_type',
            'browser', 'os', 'country', 'city', 'metadata', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def get_user_display(self, obj):
        if obj.user:
            return f"{obj.user.username} ({obj.user.email})"
        return f"Anonymous ({obj.ip_address})"
    
    def get_content_title(self, obj):
        if obj.content_object:
            return getattr(obj.content_object, 'title', str(obj.content_object))
        return None


class SystemAlertSerializer(serializers.ModelSerializer):
    """Serializer for system alerts"""
    
    alert_type_display = serializers.CharField(source='get_alert_type_display', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    resolved_by_display = serializers.SerializerMethodField()
    time_since_created = serializers.SerializerMethodField()
    
    class Meta:
        model = SystemAlert
        fields = [
            'id', 'title', 'message', 'alert_type', 'alert_type_display',
            'category', 'category_display', 'is_read', 'is_resolved',
            'resolved_by', 'resolved_by_display', 'resolved_at',
            'resolution_notes', 'priority', 'requires_action',
            'auto_dismiss_after', 'email_sent', 'slack_sent',
            'metadata', 'time_since_created', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_resolved_by_display(self, obj):
        if obj.resolved_by:
            return obj.resolved_by.username
        return None
    
    def get_time_since_created(self, obj):
        from django.utils.timesince import timesince
        return timesince(obj.created_at)


class ReportGenerationSerializer(serializers.ModelSerializer):
    """Serializer for report generation"""
    
    requested_by_display = serializers.SerializerMethodField()
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    report_format_display = serializers.CharField(source='get_report_format_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    file_size_formatted = serializers.SerializerMethodField()
    processing_time_formatted = serializers.SerializerMethodField()
    
    class Meta:
        model = ReportGeneration
        fields = [
            'id', 'name', 'report_type', 'report_type_display',
            'report_format', 'report_format_display', 'date_from', 'date_to',
            'requested_by', 'requested_by_display', 'status', 'status_display',
            'file_path', 'file_size', 'file_size_formatted', 'download_count',
            'processing_started_at', 'processing_completed_at', 'processing_time',
            'processing_time_formatted', 'error_message', 'filters',
            'include_fields', 'created_at', 'expires_at'
        ]
        read_only_fields = [
            'id', 'status', 'file_path', 'file_size', 'download_count',
            'processing_started_at', 'processing_completed_at',
            'processing_time', 'error_message', 'created_at'
        ]
    
    def get_requested_by_display(self, obj):
        return obj.requested_by.username
    
    def get_file_size_formatted(self, obj):
        if not obj.file_size:
            return "0 B"
        
        for unit in ['B', 'KB', 'MB', 'GB']:
            if obj.file_size < 1024.0:
                return f"{obj.file_size:.1f} {unit}"
            obj.file_size /= 1024.0
        return f"{obj.file_size:.1f} TB"
    
    def get_processing_time_formatted(self, obj):
        if not obj.processing_time:
            return None
        
        if obj.processing_time < 60:
            return f"{obj.processing_time:.1f} seconds"
        elif obj.processing_time < 3600:
            return f"{obj.processing_time/60:.1f} minutes"
        else:
            return f"{obj.processing_time/3600:.1f} hours"


class DashboardOverviewSerializer(serializers.Serializer):
    """Serializer for dashboard overview data"""
    
    # User statistics
    total_users = serializers.IntegerField()
    active_users_today = serializers.IntegerField()
    new_users_today = serializers.IntegerField()
    user_growth_percentage = serializers.FloatField()
    
    # Content statistics
    total_content = serializers.IntegerField()
    content_by_type = serializers.DictField()
    most_viewed_content = serializers.DictField()
    trending_content = serializers.ListField()
    
    # Engagement statistics
    total_views_today = serializers.IntegerField()
    total_likes_today = serializers.IntegerField()
    total_comments_today = serializers.IntegerField()
    total_shares_today = serializers.IntegerField()
    
    # Performance metrics
    average_session_duration = serializers.FloatField()
    bounce_rate = serializers.FloatField()
    conversion_rate = serializers.FloatField()
    
    # Recent activities
    recent_user_signups = serializers.ListField()
    recent_content_uploads = serializers.ListField()
    recent_comments = serializers.ListField()
    
    # System health
    system_alerts_count = serializers.IntegerField()
    critical_alerts_count = serializers.IntegerField()
    server_uptime = serializers.CharField()
    storage_usage_percentage = serializers.FloatField()