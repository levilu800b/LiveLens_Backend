# stories/serializers.py
# type: ignore

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

# ADDED: General StorySerializer for backward compatibility
class StorySerializer(serializers.ModelSerializer):
    """General serializer for stories - for backward compatibility"""
    author = AuthorSerializer(read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    total_pages = serializers.SerializerMethodField()
    
    class Meta:
        model = Story
        fields = (
            'id', 'title', 'slug', 'description', 'excerpt', 'category', 'tags',
            'thumbnail', 'cover_image', 'author', 'status', 'is_featured', 'is_trending',
            'read_count', 'like_count', 'comment_count', 'estimated_read_time',
            'total_pages', 'is_liked', 'is_bookmarked', 'created_at', 'updated_at', 'published_at'
        )
        read_only_fields = (
            'id', 'slug', 'author', 'read_count', 'like_count', 'comment_count',
            'excerpt', 'estimated_read_time', 'total_pages', 'is_liked', 'is_bookmarked',
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
    
    def get_total_pages(self, obj):
        """Get total number of pages in the story"""
        return obj.pages.count()

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
    related_stories = serializers.SerializerMethodField()
    
    class Meta:
        model = Story
        fields = (
            'id', 'title', 'slug', 'description', 'content', 'excerpt', 'category', 'tags',
            'thumbnail', 'cover_image', 'author', 'status', 'is_featured', 'is_trending',
            'read_count', 'like_count', 'comment_count', 'estimated_read_time',
            'pages', 'total_pages', 'is_liked', 'is_bookmarked', 'reading_progress',
            'related_stories', 'created_at', 'updated_at', 'published_at'
        )
        read_only_fields = (
            'id', 'slug', 'author', 'read_count', 'like_count', 'comment_count',
            'excerpt', 'estimated_read_time', 'created_at', 'updated_at', 'published_at'
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
    
    def get_related_stories(self, obj):
        """Get related stories based on category and tags"""
        related_stories = Story.objects.filter(
            category=obj.category,
            status='published'
        ).exclude(id=obj.id)[:5]
        
        return StoryListSerializer(
            related_stories, 
            many=True, 
            context=self.context
        ).data

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
    
    def validate_title(self, value):
        """Validate story title"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Title must be at least 3 characters long.")
        return value.strip()
    
    def validate_description(self, value):
        """Validate story description"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters long.")
        return value.strip()
    
    def validate_tags(self, value):
        """Ensure tags is a list of strings"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Tags must be a list.")
        
        if len(value) > 10:
            raise serializers.ValidationError("Maximum 10 tags allowed.")
        
        cleaned_tags = []
        for tag in value:
            if not isinstance(tag, str):
                raise serializers.ValidationError("Each tag must be a string.")
            tag = tag.strip().lower()
            if len(tag) == 0:
                continue
            if len(tag) > 50:
                raise serializers.ValidationError("Each tag must be 50 characters or less.")
            if tag not in cleaned_tags:  # Avoid duplicates
                cleaned_tags.append(tag)
        
        return cleaned_tags
    
    def validate_pages_data(self, value):
        """Validate pages data"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Pages data must be a list.")
        
        if len(value) > 100:  # Reasonable limit
            raise serializers.ValidationError("Maximum 100 pages allowed.")
        
        for i, page_data in enumerate(value):
            if not isinstance(page_data, dict):
                raise serializers.ValidationError(f"Page {i+1} data must be a dictionary.")
            
            if 'content' not in page_data:
                raise serializers.ValidationError(f"Page {i+1} must have content.")
            
            if len(page_data.get('content', '').strip()) < 10:
                raise serializers.ValidationError(f"Page {i+1} content must be at least 10 characters.")
        
        return value
    
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
                title=page_data.get('title', f'Page {i}'),
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
                    title=page_data.get('title', f'Page {i}'),
                    content=page_data.get('content', ''),
                    page_image=page_data.get('page_image')
                )
        
        return instance

class StoryInteractionSerializer(serializers.ModelSerializer):
    """Serializer for story interactions (like, bookmark, etc.)"""
    user = AuthorSerializer(read_only=True)
    story_title = serializers.CharField(source='story.title', read_only=True)
    
    class Meta:
        model = StoryInteraction
        fields = (
            'id', 'user', 'story', 'story_title', 'interaction_type',
            'last_page_read', 'reading_progress', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')
    
    def validate(self, attrs):
        """Validate interaction data"""
        interaction_type = attrs.get('interaction_type')
        last_page_read = attrs.get('last_page_read')
        reading_progress = attrs.get('reading_progress')
        
        # For reading interactions, require progress info
        if interaction_type == 'read':
            if last_page_read is None:
                raise serializers.ValidationError("last_page_read is required for read interactions")
            if reading_progress is None:
                raise serializers.ValidationError("reading_progress is required for read interactions")
        
        return attrs
    
    def create(self, validated_data):
        """Create or update interaction"""
        user = self.context['request'].user
        story = validated_data['story']
        interaction_type = validated_data['interaction_type']
        
        # For like/bookmark interactions, toggle behavior
        if interaction_type in ['like', 'bookmark']:
            interaction, created = StoryInteraction.objects.get_or_create(
                user=user,
                story=story,
                interaction_type=interaction_type
            )
            
            if not created:
                # If interaction exists, delete it (toggle off)
                interaction.delete()
                return None  # Indicate removal
        
        # For read interactions, always update
        else:
            interaction, created = StoryInteraction.objects.update_or_create(
                user=user,
                story=story,
                interaction_type=interaction_type,
                defaults=validated_data
            )
        
        return interaction

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
    
    def validate_name(self, value):
        """Validate collection name"""
        if len(value.strip()) < 3:
            raise serializers.ValidationError("Collection name must be at least 3 characters long.")
        return value.strip()
    
    def validate_story_ids(self, value):
        """Validate story IDs"""
        if len(value) > 50:  # Reasonable limit
            raise serializers.ValidationError("Maximum 50 stories allowed per collection.")
        
        # Check if all stories exist and are published
        existing_stories = Story.objects.filter(
            id__in=value,
            status='published'
        ).values_list('id', flat=True)
        
        missing_stories = set(value) - set(existing_stories)
        if missing_stories:
            raise serializers.ValidationError(
                f"Some stories not found or not published: {list(missing_stories)}"
            )
        
        return value
    
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
    archived_stories = serializers.IntegerField()
    total_reads = serializers.IntegerField()
    total_likes = serializers.IntegerField()
    total_comments = serializers.IntegerField()
    avg_read_time = serializers.FloatField()
    trending_stories = StoryListSerializer(many=True)
    featured_stories = StoryListSerializer(many=True)
    recent_stories = StoryListSerializer(many=True)
    top_categories = serializers.ListField()
    top_authors = serializers.ListField()