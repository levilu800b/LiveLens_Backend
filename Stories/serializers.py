# type: ignore

# stories/serializers.py
from rest_framework import serializers
from .models import (
    StoryCategory, Story, StoryPage, StoryIllustration, 
    StoryLike, StoryView, StoryReadingProgress
)


class StoryCategorySerializer(serializers.ModelSerializer):
    story_count = serializers.SerializerMethodField()
    
    class Meta:
        model = StoryCategory
        fields = ['id', 'name', 'slug', 'description', 'story_count', 'created_at']
        read_only_fields = ['id', 'slug', 'created_at']
    
    def get_story_count(self, obj):
        return obj.stories.filter(status='PUBLISHED').count()


class StoryIllustrationSerializer(serializers.ModelSerializer):
    image_small = serializers.ImageField(read_only=True)
    image_medium = serializers.ImageField(read_only=True)
    
    class Meta:
        model = StoryIllustration
        fields = [
            'id', 'image', 'image_small', 'image_medium', 
            'caption', 'alt_text', 'position', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class StoryPageSerializer(serializers.ModelSerializer):
    illustrations = StoryIllustrationSerializer(many=True, read_only=True)
    word_count = serializers.SerializerMethodField()
    
    class Meta:
        model = StoryPage
        fields = [
            'id', 'page_number', 'content', 'illustrations', 
            'word_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_word_count(self, obj):
        return len(obj.content.split()) if obj.content else 0


class StoryListSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.full_name', read_only=True)
    category_names = serializers.SerializerMethodField()
    thumbnail_small = serializers.ImageField(read_only=True)
    thumbnail_medium = serializers.ImageField(read_only=True)
    tag_list = serializers.ReadOnlyField()
    is_liked = serializers.SerializerMethodField()
    
    class Meta:
        model = Story
        fields = [
            'id', 'title', 'slug', 'description', 'author_name', 
            'category_names', 'tag_list', 'thumbnail', 'thumbnail_small', 
            'thumbnail_medium', 'estimated_reading_time', 'is_featured', 
            'is_trending', 'status', 'view_count', 'like_count', 
            'comment_count', 'created_at', 'published_at', 'is_liked'
        ]
    
    def get_category_names(self, obj):
        return [category.name for category in obj.categories.all()]
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False


class StoryDetailSerializer(serializers.ModelSerializer):
    author_name = serializers.CharField(source='author.full_name', read_only=True)
    categories = StoryCategorySerializer(many=True, read_only=True)
    pages = StoryPageSerializer(many=True, read_only=True)
    illustrations = StoryIllustrationSerializer(many=True, read_only=True)
    thumbnail_small = serializers.ImageField(read_only=True)
    thumbnail_medium = serializers.ImageField(read_only=True)
    tag_list = serializers.ReadOnlyField()
    is_liked = serializers.SerializerMethodField()
    user_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Story
        fields = [
            'id', 'title', 'slug', 'description', 'content', 'author_name',
            'categories', 'tag_list', 'thumbnail', 'thumbnail_small', 
            'thumbnail_medium', 'estimated_reading_time', 'is_featured',
            'is_trending', 'status', 'view_count', 'like_count', 
            'comment_count', 'share_count', 'pages', 'illustrations',
            'created_at', 'updated_at', 'published_at', 'is_liked', 
            'user_progress'
        ]
    
    def get_is_liked(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False
    
    def get_user_progress(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                progress = obj.reading_progress.get(user=request.user)
                return {
                    'current_page': progress.current_page,
                    'progress_percentage': progress.progress_percentage,
                    'completed': progress.completed,
                    'last_read_at': progress.last_read_at
                }
            except StoryReadingProgress.DoesNotExist:
                return None
        return None


class StoryCreateUpdateSerializer(serializers.ModelSerializer):
    category_ids = serializers.ListField(
        child=serializers.IntegerField(),
        write_only=True,
        required=False
    )
    
    class Meta:
        model = Story
        fields = [
            'title', 'slug', 'description', 'content', 'categories',
            'category_ids', 'tags', 'thumbnail', 'is_featured', 
            'is_trending', 'status'
        ]
        read_only_fields = ['slug']
    
    def create(self, validated_data):
        category_ids = validated_data.pop('category_ids', [])
        story = Story.objects.create(**validated_data)
        
        if category_ids:
            categories = StoryCategory.objects.filter(id__in=category_ids)
            story.categories.set(categories)
        
        return story
    
    def update(self, instance, validated_data):
        category_ids = validated_data.pop('category_ids', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if category_ids is not None:
            categories = StoryCategory.objects.filter(id__in=category_ids)
            instance.categories.set(categories)
        
        return instance


class StoryLikeSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = StoryLike
        fields = ['id', 'user_name', 'story', 'created_at']
        read_only_fields = ['id', 'user_name', 'created_at']


class StoryReadingProgressSerializer(serializers.ModelSerializer):
    story_title = serializers.CharField(source='story.title', read_only=True)
    
    class Meta:
        model = StoryReadingProgress
        fields = [
            'id', 'story', 'story_title', 'current_page', 
            'progress_percentage', 'completed', 'last_read_at'
        ]
        read_only_fields = ['id', 'story_title', 'last_read_at']