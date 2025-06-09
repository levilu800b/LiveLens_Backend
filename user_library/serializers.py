# user_library/serializers.py
# type: ignore

from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from .models import (
    UserLibrary, UserFavorites, UserPlaylist, 
    UserPlaylistItem, UserContentRecommendation, UserSearchHistory
)

class ContentObjectSerializer(serializers.Serializer):
    """
    Generic serializer for content objects
    """
    
    def to_representation(self, obj):
        if obj is None:
            return None
        
        # Basic fields that most content models should have
        data = {
            'id': str(obj.id) if hasattr(obj, 'id') else None,
            'title': getattr(obj, 'title', getattr(obj, 'name', str(obj))),
            'content_type': obj._meta.model_name,
        }
        
        # Add content-specific fields
        if hasattr(obj, 'thumbnail') and obj.thumbnail:
            data['thumbnail'] = obj.thumbnail.url if hasattr(obj.thumbnail, 'url') else str(obj.thumbnail)
        
        if hasattr(obj, 'poster') and obj.poster:
            data['poster'] = obj.poster.url if hasattr(obj.poster, 'url') else str(obj.poster)
        
        if hasattr(obj, 'duration'):
            data['duration'] = obj.duration
        
        if hasattr(obj, 'category'):
            data['category'] = obj.category
        
        if hasattr(obj, 'view_count'):
            data['view_count'] = obj.view_count
        
        if hasattr(obj, 'like_count'):
            data['like_count'] = obj.like_count
        
        if hasattr(obj, 'status'):
            data['status'] = obj.status
        
        if hasattr(obj, 'created_at'):
            data['created_at'] = obj.created_at
        
        if hasattr(obj, 'author'):
            data['author'] = obj.author.full_name if obj.author else None
        
        return data

class UserLibrarySerializer(serializers.ModelSerializer):
    """
    Serializer for user library items
    """
    
    content_object = ContentObjectSerializer(read_only=True)
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    progress_display = serializers.SerializerMethodField()
    time_spent_display = serializers.SerializerMethodField()
    
    class Meta:
        model = UserLibrary
        fields = [
            'id', 'interaction_type', 'status', 'progress_percentage',
            'current_position', 'total_duration', 'time_spent', 'view_count',
            'last_accessed', 'rating', 'notes', 'created_at', 'updated_at',
            'content_object', 'content_type_name', 'progress_display', 'time_spent_display'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'content_object']
    
    def get_progress_display(self, obj):
        """Human-readable progress display"""
        if obj.total_duration > 0:
            current_minutes = int(obj.current_position // 60)
            total_minutes = int(obj.total_duration // 60)
            return f"{current_minutes}m / {total_minutes}m ({obj.progress_percentage:.1f}%)"
        return f"{obj.progress_percentage:.1f}%"
    
    def get_time_spent_display(self, obj):
        """Human-readable time spent display"""
        hours = int(obj.time_spent // 3600)
        minutes = int((obj.time_spent % 3600) // 60)
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

class UserFavoritesSerializer(serializers.ModelSerializer):
    """
    Serializer for user favorites
    """
    
    content_object = ContentObjectSerializer(read_only=True)
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    
    class Meta:
        model = UserFavorites
        fields = [
            'id', 'favorite_type', 'created_at',
            'content_object', 'content_type_name'
        ]
        read_only_fields = ['id', 'created_at', 'content_object']

class UserPlaylistItemSerializer(serializers.ModelSerializer):
    """
    Serializer for playlist items
    """
    
    content_object = ContentObjectSerializer(read_only=True)
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    
    class Meta:
        model = UserPlaylistItem
        fields = [
            'id', 'order', 'added_at',
            'content_object', 'content_type_name'
        ]
        read_only_fields = ['id', 'added_at', 'content_object']

class UserPlaylistSerializer(serializers.ModelSerializer):
    """
    Serializer for user playlists
    """
    
    items = UserPlaylistItemSerializer(many=True, read_only=True)
    item_count = serializers.ReadOnlyField()
    
    class Meta:
        model = UserPlaylist
        fields = [
            'id', 'name', 'description', 'privacy', 'cover_image',
            'created_at', 'updated_at', 'items', 'item_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'item_count']

class UserContentRecommendationSerializer(serializers.ModelSerializer):
    """
    Serializer for content recommendations
    """
    
    content_object = ContentObjectSerializer(read_only=True)
    content_type_name = serializers.CharField(source='content_type.model', read_only=True)
    
    class Meta:
        model = UserContentRecommendation
        fields = [
            'id', 'recommendation_type', 'confidence_score', 'reason',
            'shown_count', 'clicked', 'dismissed', 'expires_at', 'created_at',
            'content_object', 'content_type_name'
        ]
        read_only_fields = ['id', 'created_at', 'content_object']