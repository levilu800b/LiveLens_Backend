# live_video/serializers.py
# type: ignore

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import LiveVideo, LiveVideoInteraction, LiveVideoComment, LiveVideoSchedule

User = get_user_model()


class LiveVideoListSerializer(serializers.ModelSerializer):
    """Serializer for live video list view (minimal data)"""
    
    author_name = serializers.CharField(source='author.username', read_only=True)
    is_live_now = serializers.BooleanField(read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    is_ended = serializers.BooleanField(read_only=True)
    duration_formatted = serializers.CharField(read_only=True)
    time_until_start = serializers.SerializerMethodField()
    stream_duration = serializers.SerializerMethodField()
    
    class Meta:
        model = LiveVideo
        fields = (
            'id', 'title', 'slug', 'short_description', 'thumbnail',
            'live_status', 'scheduled_start_time', 'scheduled_end_time',
            'host_name', 'tags', 'is_featured', 'is_premium',
            'current_viewers', 'peak_viewers', 'total_views',
            'like_count', 'comment_count', 'video_quality',
            'duration_formatted', 'author_name', 'is_live_now',
            'is_upcoming', 'is_ended', 'time_until_start',
            'stream_duration', 'created_at'
        )
        read_only_fields = (
            'id', 'slug', 'current_viewers', 'peak_viewers', 'total_views',
            'like_count', 'comment_count', 'created_at'
        )
    
    def get_time_until_start(self, obj):
        """Get formatted time until stream starts"""
        delta = obj.time_until_start
        if delta:
            total_seconds = int(delta.total_seconds())
            if total_seconds > 0:
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                if hours > 0:
                    return f"{hours}h {minutes}m"
                elif minutes > 0:
                    return f"{minutes}m {seconds}s"
                else:
                    return f"{seconds}s"
        return None
    
    def get_stream_duration(self, obj):
        """Get formatted stream duration"""
        duration = obj.stream_duration
        if duration:
            total_seconds = int(duration.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return None


class LiveVideoDetailSerializer(serializers.ModelSerializer):
    """Serializer for live video detail view (full data)"""
    
    author_name = serializers.CharField(source='author.username', read_only=True)
    author_email = serializers.CharField(source='author.email', read_only=True)
    is_live_now = serializers.BooleanField(read_only=True)
    is_upcoming = serializers.BooleanField(read_only=True)
    is_ended = serializers.BooleanField(read_only=True)
    duration_formatted = serializers.CharField(read_only=True)
    time_until_start = serializers.SerializerMethodField()
    stream_duration = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    user_watching = serializers.SerializerMethodField()
    
    class Meta:
        model = LiveVideo
        fields = (
            'id', 'title', 'slug', 'description', 'short_description',
            'thumbnail', 'video_file', 'live_status', 'scheduled_start_time',
            'scheduled_end_time', 'actual_start_time', 'actual_end_time',
            'live_stream_url', 'backup_stream_url', 'video_quality',
            'duration', 'duration_formatted', 'max_viewers',
            'host_name', 'guest_speakers', 'tags', 'is_featured',
            'is_premium', 'allow_chat', 'allow_recording',
            'current_viewers', 'peak_viewers', 'total_views',
            'like_count', 'comment_count', 'author_name', 'author_email',
            'is_live_now', 'is_upcoming', 'is_ended', 'time_until_start',
            'stream_duration', 'is_liked', 'is_bookmarked', 'user_watching',
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'slug', 'actual_start_time', 'actual_end_time',
            'current_viewers', 'peak_viewers', 'total_views',
            'like_count', 'comment_count', 'created_at', 'updated_at'
        )
    
    def get_time_until_start(self, obj):
        """Get formatted time until stream starts"""
        delta = obj.time_until_start
        if delta:
            total_seconds = int(delta.total_seconds())
            if total_seconds > 0:
                hours, remainder = divmod(total_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                if hours > 0:
                    return f"{hours}h {minutes}m"
                elif minutes > 0:
                    return f"{minutes}m {seconds}s"
                else:
                    return f"{seconds}s"
        return None
    
    def get_stream_duration(self, obj):
        """Get formatted stream duration"""
        duration = obj.stream_duration
        if duration:
            total_seconds = int(duration.total_seconds())
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return None
    
    def get_is_liked(self, obj):
        """Check if current user has liked this live video"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return LiveVideoInteraction.objects.filter(
                user=request.user,
                live_video=obj,
                interaction_type='like'
            ).exists()
        return False
    
    def get_is_bookmarked(self, obj):
        """Check if current user has bookmarked this live video"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return LiveVideoInteraction.objects.filter(
                user=request.user,
                live_video=obj,
                interaction_type='bookmark'
            ).exists()
        return False
    
    def get_user_watching(self, obj):
        """Check if current user is watching this live video"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            interaction = LiveVideoInteraction.objects.filter(
                user=request.user,
                live_video=obj,
                interaction_type='join'
            ).first()
            if interaction and not interaction.left_at:
                return True
        return False


class LiveVideoCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating live videos"""
    
    class Meta:
        model = LiveVideo
        fields = (
            'title', 'description', 'short_description', 'thumbnail',
            'video_file', 'scheduled_start_time', 'scheduled_end_time',
            'live_stream_url', 'backup_stream_url', 'stream_key',
            'video_quality', 'duration', 'max_viewers', 'host_name',
            'guest_speakers', 'tags', 'is_featured', 'is_premium',
            'allow_chat', 'allow_recording', 'auto_start'
        )
    
    def validate_title(self, value):
        """Validate live video title"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Title must be at least 2 characters long.")
        return value.strip()
    
    def validate_scheduled_start_time(self, value):
        """Validate scheduled start time"""
        if value <= timezone.now():
            raise serializers.ValidationError("Scheduled start time must be in the future.")
        return value
    
    def validate_scheduled_end_time(self, value):
        """Validate scheduled end time"""
        scheduled_start = self.initial_data.get('scheduled_start_time')
        if scheduled_start and value:
            if isinstance(scheduled_start, str):
                # Parse the string to datetime for comparison
                from django.utils.dateparse import parse_datetime
                scheduled_start = parse_datetime(scheduled_start)
            if value <= scheduled_start:
                raise serializers.ValidationError("End time must be after start time.")
        return value
    
    def validate_max_viewers(self, value):
        """Validate max viewers limit"""
        if value < 1:
            raise serializers.ValidationError("Max viewers must be at least 1.")
        if value > 100000:
            raise serializers.ValidationError("Max viewers cannot exceed 100,000.")
        return value
    
    def create(self, validated_data):
        """Create a new live video"""
        # Set the author to the current user
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class LiveVideoInteractionSerializer(serializers.ModelSerializer):
    """Serializer for live video interactions"""
    
    user_name = serializers.CharField(source='user.username', read_only=True)
    live_video_title = serializers.CharField(source='live_video.title', read_only=True)
    
    class Meta:
        model = LiveVideoInteraction
        fields = (
            'id', 'user', 'user_name', 'live_video', 'live_video_title',
            'interaction_type', 'watch_duration', 'joined_at', 'left_at',
            'created_at'
        )
        read_only_fields = ('id', 'user', 'created_at')
    
    def create(self, validated_data):
        """Create or update interaction"""
        user = self.context['request'].user
        live_video_id = self.context['live_video_id']
        interaction_type = validated_data['interaction_type']
        
        # Get the live video
        try:
            live_video = LiveVideo.objects.get(id=live_video_id)
        except LiveVideo.DoesNotExist:
            raise serializers.ValidationError("Live video not found.")
        
        # Handle different interaction types
        if interaction_type in ['like', 'bookmark']:
            # Toggle like/bookmark
            interaction, created = LiveVideoInteraction.objects.get_or_create(
                user=user,
                live_video=live_video,
                interaction_type=interaction_type,
                defaults=validated_data
            )
            
            if not created:
                # If interaction exists, remove it (toggle off)
                interaction.delete()
                return None
            
            # Update like count if it's a like
            if interaction_type == 'like':
                live_video.like_count = live_video.interactions.filter(
                    interaction_type='like'
                ).count()
                live_video.save(update_fields=['like_count'])
            
            return interaction
        
        elif interaction_type == 'join':
            # Join the live stream
            interaction, created = LiveVideoInteraction.objects.get_or_create(
                user=user,
                live_video=live_video,
                interaction_type=interaction_type,
                defaults={
                    **validated_data,
                    'joined_at': timezone.now()
                }
            )
            
            if created:
                # Increment viewer count
                live_video.increment_viewers()
                live_video.increment_total_views()
            
            return interaction
        
        elif interaction_type == 'leave':
            # Leave the live stream
            try:
                join_interaction = LiveVideoInteraction.objects.get(
                    user=user,
                    live_video=live_video,
                    interaction_type='join'
                )
                join_interaction.left_at = timezone.now()
                join_interaction.save()
                
                # Calculate watch duration
                if join_interaction.joined_at:
                    duration = (join_interaction.left_at - join_interaction.joined_at).total_seconds()
                    join_interaction.watch_duration = int(duration)
                    join_interaction.save()
                
                # Decrement viewer count
                live_video.decrement_viewers()
                
                return join_interaction
            
            except LiveVideoInteraction.DoesNotExist:
                raise serializers.ValidationError("User is not currently watching this live video.")
        
        else:
            # Create regular interaction
            interaction = LiveVideoInteraction.objects.create(
                user=user,
                live_video=live_video,
                **validated_data
            )
            return interaction


class LiveVideoCommentSerializer(serializers.ModelSerializer):
    """Serializer for live video comments (chat)"""
    
    user_name = serializers.CharField(source='user.username', read_only=True)
    user_avatar = serializers.CharField(source='user.avatar.url', read_only=True)
    time_ago = serializers.SerializerMethodField()
    
    class Meta:
        model = LiveVideoComment
        fields = (
            'id', 'live_video', 'user', 'user_name', 'user_avatar',
            'message', 'timestamp', 'is_moderator', 'is_hidden',
            'stream_time', 'time_ago'
        )
        read_only_fields = ('id', 'user', 'timestamp', 'stream_time')
    
    def get_time_ago(self, obj):
        """Get formatted time ago"""
        now = timezone.now()
        delta = now - obj.timestamp
        
        if delta.days > 0:
            return f"{delta.days}d ago"
        elif delta.seconds > 3600:
            hours = delta.seconds // 3600
            return f"{hours}h ago"
        elif delta.seconds > 60:
            minutes = delta.seconds // 60
            return f"{minutes}m ago"
        else:
            return "just now"
    
    def validate_message(self, value):
        """Validate comment message"""
        if len(value.strip()) < 1:
            raise serializers.ValidationError("Message cannot be empty.")
        if len(value) > 500:
            raise serializers.ValidationError("Message cannot exceed 500 characters.")
        return value.strip()
    
    def create(self, validated_data):
        """Create a new comment"""
        validated_data['user'] = self.context['request'].user
        validated_data['live_video_id'] = self.context['live_video_id']
        return super().create(validated_data)


class LiveVideoScheduleSerializer(serializers.ModelSerializer):
    """Serializer for live video schedules"""
    
    author_name = serializers.CharField(source='author.username', read_only=True)
    next_scheduled_date = serializers.SerializerMethodField()
    
    class Meta:
        model = LiveVideoSchedule
        fields = (
            'id', 'title_template', 'description_template', 'frequency',
            'start_time', 'duration_minutes', 'weekday', 'day_of_month',
            'is_active', 'author_name', 'next_scheduled_date',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')
    
    def get_next_scheduled_date(self, obj):
        """Get the next scheduled date based on the schedule"""
        from datetime import datetime, timedelta
        
        now = timezone.now()
        
        if obj.frequency == 'daily':
            next_date = now.date() + timedelta(days=1)
        elif obj.frequency == 'weekly' and obj.weekday is not None:
            days_ahead = obj.weekday - now.weekday()
            if days_ahead <= 0:
                days_ahead += 7
            next_date = now.date() + timedelta(days=days_ahead)
        elif obj.frequency == 'monthly' and obj.day_of_month is not None:
            if now.day < obj.day_of_month:
                next_date = now.date().replace(day=obj.day_of_month)
            else:
                if now.month == 12:
                    next_date = now.date().replace(year=now.year + 1, month=1, day=obj.day_of_month)
                else:
                    next_date = now.date().replace(month=now.month + 1, day=obj.day_of_month)
        else:
            return None
        
        return timezone.make_aware(datetime.combine(next_date, obj.start_time))
    
    def validate_title_template(self, value):
        """Validate title template"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Title template must be at least 2 characters long.")
        return value.strip()
    
    def validate_duration_minutes(self, value):
        """Validate duration"""
        if value < 1:
            raise serializers.ValidationError("Duration must be at least 1 minute.")
        if value > 1440:  # 24 hours
            raise serializers.ValidationError("Duration cannot exceed 24 hours.")
        return value
    
    def create(self, validated_data):
        """Create a new schedule"""
        validated_data['author'] = self.context['request'].user
        return super().create(validated_data)


class LiveVideoStatsSerializer(serializers.Serializer):
    """Serializer for live video statistics"""
    
    total_live_videos = serializers.IntegerField(read_only=True)
    live_now_count = serializers.IntegerField(read_only=True)
    scheduled_count = serializers.IntegerField(read_only=True)
    ended_count = serializers.IntegerField(read_only=True)
    total_viewers = serializers.IntegerField(read_only=True)
    total_views = serializers.IntegerField(read_only=True)
    average_duration = serializers.FloatField(read_only=True)
    peak_concurrent_viewers = serializers.IntegerField(read_only=True)
    most_viewed_live_video = LiveVideoListSerializer(read_only=True)
    recent_live_videos = LiveVideoListSerializer(many=True, read_only=True)