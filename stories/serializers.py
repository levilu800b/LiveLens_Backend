# type: ignore

# stories/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Story, StoryPage, StoryInteraction, StoryView, StoryCollection

User = get_user_model()

class AuthorSerializer(serializers.ModelSerializer):
    """Serializer for story author information"""
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'full_name', 'avatar')
        read_only_fields = ('id', 'username', 'first_name', 'last_name', 'full_name', 'avatar')

class StoryPageSerializer(serializers.ModelSerializer):
    """Serializer for story pages"""
    word_count = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = StoryPage
        fields = (
            'id', 'page_number', 'title', 'content', 'page_image', 
            'word_count', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'created_at', 'updated_at')

class StoryListSerializer(serializers.ModelSerializer):
    """Serializer for story list view (minimal data)"""
    author = AuthorSerializer(read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    
    class Meta:
        model = Story
        fields = (
            'id', 'title', 'slug', 'description', 'excerpt', 'category', 'tags',
            'thumbnail', 'author', 'status', 'is_featured', 'is_trending',
            'read_count', 'like_count', 'comment_count', 'estimated_read_time',
            'is_liked', 'is_bookmarked', 'created_at', 'published_at'
        )
        read_only_fields = (
            'id', 'slug', 'author', 'read_count', 'like_count', 'comment_count',
            'created_at', 'published_at'
        )
    
    def get_is_liked(self, obj):
        """Check if current user has liked this story"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return StoryInteraction.objects.filter(
                user=request.user,
                story=obj,
                interaction_type='like'
            ).exists()
        return False
    
    def get_is_bookmarked(self, obj):
        """Check if current user has bookmarked this story"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return StoryInteraction.objects.filter(
                user=request.user,
                story=obj,
                interaction_type='bookmark'
            ).exists()
        return False

class StoryDetailSerializer(serializers.ModelSerializer):
    """Serializer for story detail view (full data)"""
    author = AuthorSerializer(read_only=True)
    pages = StoryPageSerializer(many=True, read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    reading_progress = serializers.SerializerMethodField()
    total_pages = serializers.SerializerMethodField()
    
    class Meta:
        model = Story
        fields = (
            'id', 'title', 'slug', 'description', 'content', 'excerpt', 
            'category', 'tags', 'thumbnail', 'cover_image', 'author', 
            'status', 'is_featured', 'is_trending', 'read_count', 'like_count', 
            'comment_count', 'estimated_read_time', 'pages', 'total_pages',
            'is_liked', 'is_bookmarked', 'reading_progress',
            'created_at', 'updated_at', 'published_at'
        )
        read_only_fields = (
            'id', 'slug', 'author', 'read_count', 'like_count', 'comment_count',
            'created_at', 'updated_at', 'published_at'
        )
    
    def get_is_liked(self, obj):
        """Check if current user has liked this story"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return StoryInteraction.objects.filter(
                user=request.user,
                story=obj,
                interaction_type='like'
            ).exists()
        return False
    
    def get_is_bookmarked(self, obj):
        """Check if current user has bookmarked this story"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return StoryInteraction.objects.filter(
                user=request.user,
                story=obj,
                interaction_type='bookmark'
            ).exists()
        return False
    
    def get_reading_progress(self, obj):
        """Get user's reading progress for this story"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                interaction = StoryInteraction.objects.get(
                    user=request.user,
                    story=obj,
                    interaction_type='read'
                )
                return {
                    'last_page_read': interaction.last_page_read,
                    'progress_percentage': interaction.reading_progress
                }
            except StoryInteraction.DoesNotExist:
                pass
        return None
    
    def get_total_pages(self, obj):
        """Get total number of pages in the story"""
        return obj.pages.count()

class StoryCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating stories"""
    pages_data = serializers.ListField(
        child=serializers.DictField(),
        write_only=True,
        required=False,
        help_text="List of page data for paginated content"
    )
    
    class Meta:
        model = Story
        fields = (
            'title', 'description', 'content', 'category', 'tags',
            'thumbnail', 'cover_image', 'status', 'is_featured', 
            'is_trending', 'pages_data'
        )
    
    def validate_tags(self, value):
        """Ensure tags is a list of strings"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Tags must be a list.")
        
        for tag in value:
            if not isinstance(tag, str):
                raise serializers.ValidationError("Each tag must be a string.")
            if len(tag.strip()) == 0:
                raise serializers.ValidationError("Tags cannot be empty.")
        
        return [tag.strip().lower() for tag in value if tag.strip()]
    
    def create(self, validated_data):
        """Create story with optional pages"""
        pages_data = validated_data.pop('pages_data', [])
        validated_data['author'] = self.context['request'].user
        
        # Set published_at if status is published
        if validated_data.get('status') == 'published':
            validated_data['published_at'] = timezone.now()
        
        story = Story.objects.create(**validated_data)
        
        # Create pages if provided
        for i, page_data in enumerate(pages_data, 1):
            StoryPage.objects.create(
                story=story,
                page_number=i,
                title=page_data.get('title', ''),
                content=page_data.get('content', ''),
                page_image=page_data.get('page_image')
            )
        
        return story
    
    def update(self, instance, validated_data):
        """Update story and optionally update pages"""
        pages_data = validated_data.pop('pages_data', None)
        
        # Update published_at if status changes to published
        if (validated_data.get('status') == 'published' and 
            instance.status != 'published'):
            validated_data['published_at'] = timezone.now()
        
        # Update story fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update pages if provided
        if pages_data is not None:
            # Delete existing pages
            instance.pages.all().delete()
            
            # Create new pages
            for i, page_data in enumerate(pages_data, 1):
                StoryPage.objects.create(
                    story=instance,
                    page_number=i,
                    title=page_data.get('title', ''),
                    content=page_data.get('content', ''),
                    page_image=page_data.get('page_image')
                )
        
        return instance

class StoryInteractionSerializer(serializers.ModelSerializer):
    """Serializer for story interactions (like, bookmark, etc.)"""
    
    class Meta:
        model = StoryInteraction
        fields = (
            'id', 'interaction_type', 'last_page_read', 'reading_progress',
            'created_at'
        )
        read_only_fields = ('id', 'created_at')
    
    def create(self, validated_data):
        """Create or update interaction"""
        user = self.context['request'].user
        story = self.context['story']
        interaction_type = validated_data['interaction_type']
        
        # For like and bookmark, toggle the interaction
        if interaction_type in ['like', 'bookmark']:
            interaction, created = StoryInteraction.objects.get_or_create(
                user=user,
                story=story,
                interaction_type=interaction_type,
                defaults=validated_data
            )
            
            if not created:
                # If interaction exists, delete it (toggle off)
                interaction.delete()
                return None
            
            return interaction
        
        # For read interaction, update if exists
        elif interaction_type == 'read':
            interaction, created = StoryInteraction.objects.update_or_create(
                user=user,
                story=story,
                interaction_type=interaction_type,
                defaults=validated_data
            )
            return interaction
        
        return StoryInteraction.objects.create(
            user=user,
            story=story,
            **validated_data
        )

class StoryCollectionSerializer(serializers.ModelSerializer):
    """Serializer for story collections"""
    user = AuthorSerializer(read_only=True)
    stories = StoryListSerializer(many=True, read_only=True)
    story_count = serializers.IntegerField(read_only=True)
    story_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        help_text="List of story IDs to add to collection"
    )
    
    class Meta:
        model = StoryCollection
        fields = (
            'id', 'name', 'description', 'user', 'stories', 'story_count',
            'story_ids', 'is_public', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        """Create collection with stories"""
        story_ids = validated_data.pop('story_ids', [])
        validated_data['user'] = self.context['request'].user
        
        collection = StoryCollection.objects.create(**validated_data)
        
        if story_ids:
            stories = Story.objects.filter(id__in=story_ids, status='published')
            collection.stories.set(stories)
        
        return collection
    
    def update(self, instance, validated_data):
        """Update collection and stories"""
        story_ids = validated_data.pop('story_ids', None)
        
        # Update collection fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update stories if provided
        if story_ids is not None:
            stories = Story.objects.filter(id__in=story_ids, status='published')
            instance.stories.set(stories)
        
        return instance

class StoryViewSerializer(serializers.ModelSerializer):
    """Serializer for tracking story views"""
    
    class Meta:
        model = StoryView
        fields = (
            'time_spent', 'pages_viewed'
        )
    
    def create(self, validated_data):
        """Create story view with request data"""
        request = self.context['request']
        story = self.context['story']
        
        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        return StoryView.objects.create(
            story=story,
            user=request.user if request.user.is_authenticated else None,
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            **validated_data
        )

class StoryStatsSerializer(serializers.Serializer):
    """Serializer for story statistics"""
    total_stories = serializers.IntegerField()
    published_stories = serializers.IntegerField()
    draft_stories = serializers.IntegerField()
    total_reads = serializers.IntegerField()
    total_likes = serializers.IntegerField()
    trending_stories = StoryListSerializer(many=True)
    featured_stories = StoryListSerializer(many=True)
    recent_stories = StoryListSerializer(many=True)