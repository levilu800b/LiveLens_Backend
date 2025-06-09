# sneak_peeks/serializers.py
# type: ignore

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    SneakPeek, SneakPeekView, SneakPeekInteraction, 
    SneakPeekPlaylist, SneakPeekPlaylistItem
)

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for sneak peeks"""
    
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'avatar_url']
        read_only_fields = ['id', 'username']
    
    def get_avatar_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None


class SneakPeekListSerializer(serializers.ModelSerializer):
    """Serializer for sneak peek list view (minimal data)"""
    
    author = UserBasicSerializer(read_only=True)
    duration_formatted = serializers.CharField(read_only=True)
    file_size_formatted = serializers.CharField(read_only=True)
    tags_list = serializers.SerializerMethodField()
    user_interaction = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    
    class Meta:
        model = SneakPeek
        fields = [
            'id', 'title', 'slug', 'short_description', 'author', 'category',
            'tags_list', 'thumbnail_url', 'duration', 'duration_formatted',
            'video_quality', 'file_size_formatted', 'release_date',
            'content_rating', 'is_featured', 'is_trending', 'is_premium',
            'view_count', 'like_count', 'dislike_count', 'comment_count',
            'created_at', 'published_at', 'user_interaction'
        ]
        read_only_fields = [
            'id', 'slug', 'author', 'view_count', 'like_count', 
            'dislike_count', 'comment_count', 'created_at', 'published_at'
        ]
    
    def get_tags_list(self, obj):
        return obj.get_tags_list()
    
    def get_user_interaction(self, obj):
        """Get current user's interaction with this sneak peek"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            interactions = SneakPeekInteraction.objects.filter(
                user=request.user, 
                sneak_peek=obj
            ).values_list('interaction_type', flat=True)
            return list(interactions)
        return []
    
    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            return obj.thumbnail.url
        return None


class SneakPeekDetailSerializer(serializers.ModelSerializer):
    """Serializer for sneak peek detail view (full data)"""
    
    author = UserBasicSerializer(read_only=True)
    duration_formatted = serializers.CharField(read_only=True)
    file_size_formatted = serializers.CharField(read_only=True)
    tags_list = serializers.SerializerMethodField()
    user_interaction = serializers.SerializerMethodField()
    related_sneak_peeks = serializers.SerializerMethodField()
    video_url = serializers.SerializerMethodField()
    thumbnail_url = serializers.SerializerMethodField()
    poster_url = serializers.SerializerMethodField()
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    
    class Meta:
        model = SneakPeek
        fields = [
            'id', 'title', 'slug', 'description', 'short_description',
            'author', 'category', 'tags', 'tags_list', 'video_url',
            'thumbnail_url', 'poster_url', 'duration', 'duration_formatted',
            'video_quality', 'file_size', 'file_size_formatted', 'release_date',
            'content_rating', 'status', 'is_featured', 'is_trending', 
            'is_premium', 'view_count', 'like_count', 'dislike_count',
            'share_count', 'comment_count', 'meta_title', 'meta_description',
            'meta_keywords', 'related_content_type', 'related_content_id',
            'created_at', 'updated_at', 'published_at', 'user_interaction',
            'related_sneak_peeks', 'can_edit', 'can_delete'
        ]
        read_only_fields = [
            'id', 'slug', 'author', 'file_size', 'view_count', 'like_count',
            'dislike_count', 'share_count', 'comment_count', 'created_at',
            'updated_at', 'published_at'
        ]
    
    def get_tags_list(self, obj):
        return obj.get_tags_list()
    
    def get_user_interaction(self, obj):
        """Get current user's interactions with this sneak peek"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            interactions = SneakPeekInteraction.objects.filter(
                user=request.user, 
                sneak_peek=obj
            ).values_list('interaction_type', flat=True)
            return list(interactions)
        return []
    
    def get_related_sneak_peeks(self, obj):
        """Get related sneak peeks"""
        related = obj.get_related_sneak_peeks(limit=5)
        return SneakPeekListSerializer(
            related, 
            many=True, 
            context=self.context
        ).data
    
    def get_video_url(self, obj):
        if obj.video_file:
            return obj.video_file.url
        return None
    
    def get_thumbnail_url(self, obj):
        if obj.thumbnail:
            return obj.thumbnail.url
        return None
    
    def get_poster_url(self, obj):
        if obj.poster:
            return obj.poster.url
        return None
    
    def get_can_edit(self, obj):
        """Check if current user can edit this sneak peek"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.author == request.user or request.user.is_admin
    
    def get_can_delete(self, obj):
        """Check if current user can delete this sneak peek"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.author == request.user or request.user.is_admin


class SneakPeekCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating sneak peeks"""
    
    tags_list = serializers.ListField(
        child=serializers.CharField(max_length=50),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = SneakPeek
        fields = [
            'title', 'description', 'short_description', 'category',
            'tags', 'tags_list', 'video_file', 'thumbnail', 'poster',
            'duration', 'video_quality', 'release_date', 'content_rating',
            'status', 'is_featured', 'is_trending', 'is_premium',
            'meta_title', 'meta_description', 'meta_keywords',
            'related_content_type', 'related_content_id'
        ]
    
    def validate_tags_list(self, value):
        """Validate tags list"""
        if len(value) > 10:
            raise serializers.ValidationError("Maximum 10 tags allowed")
        
        for tag in value:
            if len(tag.strip()) < 2:
                raise serializers.ValidationError("Each tag must be at least 2 characters")
        
        return value
    
    def validate_duration(self, value):
        """Validate duration"""
        if value < 0:
            raise serializers.ValidationError("Duration cannot be negative")
        if value > 600:  # 10 minutes max for sneak peeks
            raise serializers.ValidationError("Sneak peeks cannot be longer than 10 minutes")
        return value
    
    def validate_video_file(self, value):
        """Validate video file"""
        if not value:
            raise serializers.ValidationError("Video file is required")
        return value
    
    def create(self, validated_data):
        """Create a new sneak peek"""
        tags_list = validated_data.pop('tags_list', [])
        
        # Convert tags list to comma-separated string
        if tags_list:
            validated_data['tags'] = ', '.join([tag.strip() for tag in tags_list])
        
        sneak_peek = SneakPeek.objects.create(**validated_data)
        return sneak_peek
    
    def update(self, instance, validated_data):
        """Update an existing sneak peek"""
        tags_list = validated_data.pop('tags_list', None)
        
        # Convert tags list to comma-separated string
        if tags_list is not None:
            validated_data['tags'] = ', '.join([tag.strip() for tag in tags_list])
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance


class SneakPeekInteractionSerializer(serializers.ModelSerializer):
    """Serializer for sneak peek interactions"""
    
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = SneakPeekInteraction
        fields = [
            'id', 'user', 'interaction_type', 'share_platform', 'rating', 'created_at'
        ]
        read_only_fields = ['id', 'user', 'created_at']


class SneakPeekViewSerializer(serializers.ModelSerializer):
    """Serializer for sneak peek views"""
    
    user = UserBasicSerializer(read_only=True)
    sneak_peek = SneakPeekListSerializer(read_only=True)
    
    class Meta:
        model = SneakPeekView
        fields = [
            'id', 'sneak_peek', 'user', 'device_type', 'watch_duration',
            'completion_percentage', 'referrer', 'utm_source', 'utm_medium',
            'utm_campaign', 'viewed_at'
        ]
        read_only_fields = ['id', 'sneak_peek', 'user', 'viewed_at']


class SneakPeekPlaylistItemSerializer(serializers.ModelSerializer):
    """Serializer for playlist items"""
    
    sneak_peek = SneakPeekListSerializer(read_only=True)
    
    class Meta:
        model = SneakPeekPlaylistItem
        fields = ['id', 'sneak_peek', 'order', 'added_at']
        read_only_fields = ['id', 'added_at']


class SneakPeekPlaylistSerializer(serializers.ModelSerializer):
    """Serializer for sneak peek playlists"""
    
    creator = UserBasicSerializer(read_only=True)
    sneak_peeks = SneakPeekPlaylistItemSerializer(
        source='sneakpeekplaylistitem_set',
        many=True, 
        read_only=True
    )
    sneak_peek_count = serializers.IntegerField(read_only=True)
    total_duration = serializers.IntegerField(read_only=True)
    can_edit = serializers.SerializerMethodField()
    
    class Meta:
        model = SneakPeekPlaylist
        fields = [
            'id', 'name', 'description', 'creator', 'sneak_peeks',
            'sneak_peek_count', 'total_duration', 'is_public', 'is_auto_play',
            'created_at', 'updated_at', 'can_edit'
        ]
        read_only_fields = ['id', 'creator', 'created_at', 'updated_at']
    
    def get_can_edit(self, obj):
        """Check if current user can edit this playlist"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.creator == request.user or request.user.is_admin


class SneakPeekPlaylistCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating playlists"""
    
    sneak_peek_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = SneakPeekPlaylist
        fields = [
            'name', 'description', 'is_public', 'is_auto_play', 'sneak_peek_ids'
        ]
    
    def validate_name(self, value):
        """Validate playlist name"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Playlist name must be at least 3 characters")
        return value.strip()
    
    def validate_sneak_peek_ids(self, value):
        """Validate sneak peek IDs"""
        if len(value) > 100:
            raise serializers.ValidationError("Maximum 100 sneak peeks per playlist")
        
        # Check if all sneak peeks exist and are published
        existing_ids = SneakPeek.objects.filter(
            id__in=value,
            status='published'
        ).values_list('id', flat=True)
        
        invalid_ids = set(value) - set(existing_ids)
        if invalid_ids:
            raise serializers.ValidationError(
                f"Invalid or unpublished sneak peek IDs: {list(invalid_ids)}"
            )
        
        return value
    
    def create(self, validated_data):
        """Create a new playlist"""
        sneak_peek_ids = validated_data.pop('sneak_peek_ids', [])
        
        playlist = SneakPeekPlaylist.objects.create(**validated_data)
        
        # Add sneak peeks to playlist
        for order, sneak_peek_id in enumerate(sneak_peek_ids):
            SneakPeekPlaylistItem.objects.create(
                playlist=playlist,
                sneak_peek_id=sneak_peek_id,
                order=order
            )
        
        return playlist
    
    def update(self, instance, validated_data):
        """Update an existing playlist"""
        sneak_peek_ids = validated_data.pop('sneak_peek_ids', None)
        
        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update sneak peeks if provided
        if sneak_peek_ids is not None:
            # Remove existing items
            instance.sneakpeekplaylistitem_set.all().delete()
            
            # Add new items
            for order, sneak_peek_id in enumerate(sneak_peek_ids):
                SneakPeekPlaylistItem.objects.create(
                    playlist=instance,
                    sneak_peek_id=sneak_peek_id,
                    order=order
                )
        
        return instance


class SneakPeekStatsSerializer(serializers.Serializer):
    """Serializer for sneak peek statistics"""
    
    total_sneak_peeks = serializers.IntegerField()
    total_views = serializers.IntegerField()
    total_likes = serializers.IntegerField()
    total_comments = serializers.IntegerField()
    average_rating = serializers.FloatField()
    most_viewed = SneakPeekListSerializer()
    most_liked = SneakPeekListSerializer()
    trending_sneak_peeks = SneakPeekListSerializer(many=True)
    recent_sneak_peeks = SneakPeekListSerializer(many=True)