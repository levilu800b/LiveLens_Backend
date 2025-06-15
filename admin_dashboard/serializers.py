# ===================================================================
# admin_dashboard/serializers.py
# type: ignore

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.db.models import Count, Sum, Avg, Q
from django.utils import timezone
from datetime import timedelta, date
from .models import AdminActivity, PlatformStatistics, ContentModerationQueue

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user information"""
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'avatar_url', 'is_staff', 'is_active', 'date_joined', 'last_login']
        read_only_fields = ['id', 'date_joined']
    
    def get_avatar_url(self, obj):
        return obj.avatar.url if obj.avatar else None


class AdminActivitySerializer(serializers.ModelSerializer):
    """Serializer for admin activities"""
    admin = UserBasicSerializer(read_only=True)
    content_type_name = serializers.CharField(source='content_type.name', read_only=True)
    
    class Meta:
        model = AdminActivity
        fields = ['id', 'admin', 'activity_type', 'description', 'content_type_name', 'object_id', 'metadata', 'ip_address', 'timestamp']
        read_only_fields = ['id', 'timestamp']


class PlatformStatisticsSerializer(serializers.ModelSerializer):
    """Serializer for platform statistics"""
    
    class Meta:
        model = PlatformStatistics
        fields = '__all__'
        read_only_fields = ['id', 'created_at', 'updated_at']


class ContentModerationQueueSerializer(serializers.ModelSerializer):
    """Serializer for content moderation queue"""
    submitted_by = UserBasicSerializer(read_only=True)
    reviewed_by = UserBasicSerializer(read_only=True)
    content_type_name = serializers.CharField(source='content_type.name', read_only=True)
    
    class Meta:
        model = ContentModerationQueue
        fields = ['id', 'content_type_name', 'object_id', 'submitted_by', 'reviewed_by', 'status', 'priority', 'reason', 'review_notes', 'submitted_at', 'reviewed_at']
        read_only_fields = ['id', 'submitted_at']


class DashboardStatsSerializer(serializers.Serializer):
    """Comprehensive dashboard statistics"""
    
    # Overview Stats
    total_users = serializers.IntegerField()
    new_users_today = serializers.IntegerField()
    active_users_today = serializers.IntegerField()
    verified_users = serializers.IntegerField()
    
    # Content Stats
    total_stories = serializers.IntegerField()
    total_films = serializers.IntegerField()
    total_content = serializers.IntegerField()
    total_podcasts = serializers.IntegerField()
    total_animations = serializers.IntegerField()
    total_sneak_peeks = serializers.IntegerField()
    total_live_videos = serializers.IntegerField()
    total_all_content = serializers.IntegerField()
    
    # Engagement Stats
    total_comments = serializers.IntegerField()
    total_likes = serializers.IntegerField()
    total_views = serializers.IntegerField()
    
    # Trending Content (Top 5 each)
    trending_stories = serializers.ListField()
    trending_films = serializers.ListField()
    trending_podcasts = serializers.ListField()
    trending_animations = serializers.ListField()
    
    # Most Active Users
    most_active_users = serializers.ListField()
    
    # Recent Activities
    recent_activities = AdminActivitySerializer(many=True)
    
    # Moderation Queue
    pending_moderation = serializers.IntegerField()
    
    # Performance Metrics
    avg_session_duration = serializers.FloatField()
    bounce_rate = serializers.FloatField()


class ContentManagementSerializer(serializers.Serializer):
    """Serializer for content management data"""
    content_type = serializers.CharField()
    content_id = serializers.IntegerField()
    title = serializers.CharField()
    author = serializers.CharField()
    status = serializers.CharField()
    views = serializers.IntegerField()
    likes = serializers.IntegerField()
    comments = serializers.IntegerField()
    created_at = serializers.DateTimeField()
    is_featured = serializers.BooleanField()
    is_trending = serializers.BooleanField()


class UserManagementSerializer(serializers.ModelSerializer):
    """Extended user serializer for admin management"""
    avatar_url = serializers.SerializerMethodField()
    total_content = serializers.SerializerMethodField()
    total_comments = serializers.SerializerMethodField()
    last_activity = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name', 'avatar_url',
            'is_staff', 'is_active', 'is_verified', 'date_joined', 'last_login',
            'total_content', 'total_comments', 'last_activity'
        ]
        read_only_fields = ['id', 'date_joined']
    
    def get_avatar_url(self, obj):
        return obj.avatar.url if obj.avatar else None
    
    def get_total_content(self, obj):
        # This will need to be calculated based on actual content models
        from stories.models import Story
        try:
            return Story.objects.filter(author=obj).count()
        except:
            return 0
    
    def get_total_comments(self, obj):
        from comments.models import Comment
        try:
            return Comment.objects.filter(user=obj).count()
        except:
            return 0
    
    def get_last_activity(self, obj):
        return obj.last_login

