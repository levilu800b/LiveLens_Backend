# comments/serializers.py
# type: ignore

from rest_framework import serializers
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from .models import Comment, CommentInteraction, CommentNotification
import bleach

User = get_user_model()

class UserBasicSerializer(serializers.ModelSerializer):
    """Basic user info for comments"""
    
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'avatar_url', 'is_admin']
        read_only_fields = ['id', 'username', 'is_admin']
    
    def get_avatar_url(self, obj):
        if obj.avatar:
            return obj.avatar.url
        return None


class CommentInteractionSerializer(serializers.ModelSerializer):
    """Serializer for comment interactions"""
    
    user = UserBasicSerializer(read_only=True)
    
    class Meta:
        model = CommentInteraction
        fields = ['id', 'user', 'interaction_type', 'report_reason', 'report_description', 'created_at']
        read_only_fields = ['id', 'user', 'created_at']


class CommentReplySerializer(serializers.ModelSerializer):
    """Serializer for comment replies (simplified to avoid deep nesting)"""
    
    user = UserBasicSerializer(read_only=True)
    user_interaction = serializers.SerializerMethodField()
    time_since = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'text', 'like_count', 'dislike_count', 
            'is_edited', 'edited_at', 'status', 'created_at', 
            'user_interaction', 'time_since'
        ]
        read_only_fields = [
            'id', 'user', 'like_count', 'dislike_count', 
            'is_edited', 'edited_at', 'status', 'created_at'
        ]
    
    def get_user_interaction(self, obj):
        """Get current user's interaction with this comment"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            interaction = CommentInteraction.objects.filter(
                user=request.user, 
                comment=obj
            ).first()
            if interaction:
                return interaction.interaction_type
        return None
    
    def get_time_since(self, obj):
        """Get human-readable time since comment was posted"""
        from django.utils.timesince import timesince
        return timesince(obj.created_at)
    
    def validate_text(self, value):
        """Clean and validate comment text"""
        # Remove potentially harmful HTML tags
        allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'br']
        cleaned_text = bleach.clean(value, tags=allowed_tags, strip=True)
        
        if len(cleaned_text.strip()) < 1:
            raise serializers.ValidationError("Comment cannot be empty")
        
        return cleaned_text


class CommentSerializer(serializers.ModelSerializer):
    """Main comment serializer with full details"""
    
    user = UserBasicSerializer(read_only=True)
    replies = CommentReplySerializer(many=True, read_only=True, source='get_replies')
    reply_count = serializers.IntegerField(read_only=True)
    user_interaction = serializers.SerializerMethodField()
    content_title = serializers.SerializerMethodField()
    time_since = serializers.SerializerMethodField()
    thread_level = serializers.IntegerField(read_only=True)
    can_edit = serializers.SerializerMethodField()
    can_delete = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = [
            'id', 'user', 'text', 'parent', 'status', 'like_count', 
            'dislike_count', 'reply_count', 'replies', 'is_edited', 
            'edited_at', 'is_flagged', 'created_at', 'updated_at',
            'user_interaction', 'content_title', 'time_since', 
            'thread_level', 'can_edit', 'can_delete'
        ]
        read_only_fields = [
            'id', 'user', 'status', 'like_count', 'dislike_count', 
            'reply_count', 'replies', 'is_edited', 'edited_at', 
            'is_flagged', 'created_at', 'updated_at', 'thread_level'
        ]
    
    def get_user_interaction(self, obj):
        """Get current user's interaction with this comment"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            interaction = CommentInteraction.objects.filter(
                user=request.user, 
                comment=obj
            ).first()
            if interaction:
                return interaction.interaction_type
        return None
    
    def get_content_title(self, obj):
        """Get the title of the content this comment is on"""
        if obj.content_object:
            return getattr(obj.content_object, 'title', str(obj.content_object))
        return "Unknown Content"
    
    def get_time_since(self, obj):
        """Get human-readable time since comment was posted"""
        from django.utils.timesince import timesince
        return timesince(obj.created_at)
    
    def get_can_edit(self, obj):
        """Check if current user can edit this comment"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        # Users can edit their own comments within 15 minutes
        from django.utils import timezone
        from datetime import timedelta
        
        if obj.user == request.user:
            time_limit = obj.created_at + timedelta(minutes=15)
            return timezone.now() < time_limit
        
        # Admins can always edit
        return request.user.is_admin
    
    def get_can_delete(self, obj):
        """Check if current user can delete this comment"""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        # Users can delete their own comments, admins can delete any
        return obj.user == request.user or request.user.is_admin
    
    def validate_text(self, value):
        """Clean and validate comment text"""
        # Remove potentially harmful HTML tags
        allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'br']
        cleaned_text = bleach.clean(value, tags=allowed_tags, strip=True)
        
        if len(cleaned_text.strip()) < 1:
            raise serializers.ValidationError("Comment cannot be empty")
        
        return cleaned_text
    
    def validate_parent(self, value):
        """Validate parent comment"""
        if value:
            # Check if parent exists and is on the same content
            if not Comment.objects.filter(id=value.id).exists():
                raise serializers.ValidationError("Parent comment does not exist")
            
            # Limit nesting depth
            if value.thread_level >= 5:  # Max 5 levels of nesting
                raise serializers.ValidationError("Maximum comment nesting depth reached")
        
        return value


class CommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating new comments"""
    
    content_type_name = serializers.CharField(write_only=True)
    object_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Comment
        fields = ['text', 'parent', 'content_type_name', 'object_id']
    
    def validate_content_type_name(self, value):
        """Validate and get content type"""
        valid_content_types = [
            'story', 'film', 'content', 'podcast', 'animation', 'sneakpeek'
        ]
        
        if value not in valid_content_types:
            raise serializers.ValidationError(
                f"Invalid content type. Must be one of: {', '.join(valid_content_types)}"
            )
        
        # Map content type names to model names
        content_type_mapping = {
            'story': 'story',
            'film': 'film',
            'content': 'content',
            'podcast': 'podcast',
            'animation': 'animation',
            'sneakpeek': 'sneakpeek'
        }
        
        model_name = content_type_mapping[value]
        
        try:
            content_type = ContentType.objects.get(model=model_name)
            return content_type
        except ContentType.DoesNotExist:
            raise serializers.ValidationError(f"Content type '{value}' not found")
    
    def validate_object_id(self, value):
        """Validate that the object exists"""
        # This will be validated against the actual content type in create method
        return value
    
    def validate_text(self, value):
        """Clean and validate comment text"""
        allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'br']
        cleaned_text = bleach.clean(value, tags=allowed_tags, strip=True)
        
        if len(cleaned_text.strip()) < 1:
            raise serializers.ValidationError("Comment cannot be empty")
        
        return cleaned_text
    
    def create(self, validated_data):
        """Create a new comment"""
        content_type = validated_data.pop('content_type_name')
        object_id = validated_data.pop('object_id')
        
        # Verify the object exists
        try:
            content_object = content_type.get_object_for_this_type(id=object_id)
        except content_type.model_class().DoesNotExist:
            raise serializers.ValidationError("Content object does not exist")
        
        # Create the comment
        comment = Comment.objects.create(
            content_type=content_type,
            object_id=object_id,
            **validated_data
        )
        
        return comment


class CommentUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating comments"""
    
    class Meta:
        model = Comment
        fields = ['text']
    
    def validate_text(self, value):
        """Clean and validate comment text"""
        allowed_tags = ['b', 'i', 'u', 'em', 'strong', 'br']
        cleaned_text = bleach.clean(value, tags=allowed_tags, strip=True)
        
        if len(cleaned_text.strip()) < 1:
            raise serializers.ValidationError("Comment cannot be empty")
        
        return cleaned_text
    
    def update(self, instance, validated_data):
        """Update comment and mark as edited"""
        instance.text = validated_data.get('text', instance.text)
        instance.mark_as_edited()
        return instance


class CommentInteractionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating comment interactions"""
    
    class Meta:
        model = CommentInteraction
        fields = ['interaction_type', 'report_reason', 'report_description']
    
    def validate_interaction_type(self, value):
        """Validate interaction type"""
        if value not in ['like', 'dislike', 'report']:
            raise serializers.ValidationError("Invalid interaction type")
        return value
    
    def validate(self, data):
        """Validate report fields if reporting"""
        if data.get('interaction_type') == 'report':
            if not data.get('report_reason'):
                raise serializers.ValidationError("Report reason is required when reporting")
        return data


class CommentNotificationSerializer(serializers.ModelSerializer):
    """Serializer for comment notifications"""
    
    sender = UserBasicSerializer(read_only=True)
    comment = CommentSerializer(read_only=True)
    time_since = serializers.SerializerMethodField()
    
    class Meta:
        model = CommentNotification
        fields = [
            'id', 'sender', 'comment', 'notification_type', 'message',
            'is_read', 'read_at', 'created_at', 'time_since'
        ]
        read_only_fields = ['id', 'sender', 'comment', 'created_at']
    
    def get_time_since(self, obj):
        """Get human-readable time since notification was created"""
        from django.utils.timesince import timesince
        return timesince(obj.created_at)