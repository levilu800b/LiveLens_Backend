# media_content/serializers.py
# type: ignore

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import (
    Film, Content, MediaInteraction, MediaView, MediaCollection, 
    Playlist, PlaylistItem
)

User = get_user_model()

class AuthorSerializer(serializers.ModelSerializer):
    """Serializer for content author information"""
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'full_name', 'avatar')
        read_only_fields = ('id', 'username', 'first_name', 'last_name', 'full_name', 'avatar')

class BaseMediaSerializer(serializers.ModelSerializer):
    """Base serializer for common media fields"""
    author = AuthorSerializer(read_only=True)
    duration_formatted = serializers.CharField(read_only=True)
    trailer_duration_formatted = serializers.CharField(read_only=True)
    file_size_formatted = serializers.CharField(read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()
    watch_progress = serializers.SerializerMethodField()
    
    def get_is_liked(self, obj):
        """Check if current user has liked this content"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            content_type = 'film' if isinstance(obj, Film) else 'content'
            return MediaInteraction.objects.filter(
                user=request.user,
                content_type=content_type,
                object_id=obj.id,
                interaction_type='like'
            ).exists()
        return False
    
    def get_is_bookmarked(self, obj):
        """Check if current user has bookmarked this content"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            content_type = 'film' if isinstance(obj, Film) else 'content'
            return MediaInteraction.objects.filter(
                user=request.user,
                content_type=content_type,
                object_id=obj.id,
                interaction_type='bookmark'
            ).exists()
        return False
    
    def get_user_rating(self, obj):
        """Get current user's rating for this content"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                content_type = 'film' if isinstance(obj, Film) else 'content'
                interaction = MediaInteraction.objects.get(
                    user=request.user,
                    content_type=content_type,
                    object_id=obj.id,
                    interaction_type='rate'
                )
                return interaction.rating
            except MediaInteraction.DoesNotExist:
                pass
        return None
    
    def get_watch_progress(self, obj):
        """Get user's watch progress for this content"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                content_type = 'film' if isinstance(obj, Film) else 'content'
                interaction = MediaInteraction.objects.get(
                    user=request.user,
                    content_type=content_type,
                    object_id=obj.id,
                    interaction_type='watch'
                )
                return {
                    'progress_percentage': interaction.watch_progress,
                    'watch_time': interaction.watch_time
                }
            except MediaInteraction.DoesNotExist:
                pass
        return None

# ADDED: General serializers for backward compatibility
class FilmSerializer(BaseMediaSerializer):
    """General serializer for films - for backward compatibility"""
    
    class Meta:
        model = Film
        fields = (
            'id', 'title', 'slug', 'description', 'short_description', 'category', 'tags',
            'thumbnail', 'poster', 'banner', 'video_file', 'trailer_file',
            'author', 'status', 'is_featured', 'is_trending', 'is_premium',
            'view_count', 'like_count', 'comment_count', 'download_count',
            'average_rating', 'rating_count', 'duration', 'duration_formatted',
            'trailer_duration', 'trailer_duration_formatted', 'video_quality',
            'file_size', 'file_size_formatted', 'release_year', 'language',
            'subtitles_available', 'director', 'cast', 'producer', 'studio',
            'budget', 'box_office', 'mpaa_rating', 'is_series', 'series_name',
            'episode_number', 'season_number', 'is_liked', 'is_bookmarked',
            'user_rating', 'watch_progress', 'created_at', 'updated_at', 'published_at'
        )
        read_only_fields = (
            'id', 'slug', 'author', 'view_count', 'like_count', 'comment_count',
            'download_count', 'average_rating', 'rating_count', 'duration_formatted',
            'trailer_duration_formatted', 'file_size_formatted', 'is_liked', 
            'is_bookmarked', 'user_rating', 'watch_progress', 'created_at', 
            'updated_at', 'published_at'
        )

class ContentSerializer(BaseMediaSerializer):
    """General serializer for content - for backward compatibility"""
    
    class Meta:
        model = Content
        fields = (
            'id', 'title', 'slug', 'description', 'short_description', 'category', 'tags',
            'thumbnail', 'poster', 'banner', 'video_file', 'trailer_file',
            'author', 'status', 'is_featured', 'is_trending', 'is_premium',
            'view_count', 'like_count', 'comment_count', 'download_count',
            'average_rating', 'rating_count', 'duration', 'duration_formatted',
            'trailer_duration', 'trailer_duration_formatted', 'video_quality',
            'file_size', 'file_size_formatted', 'release_year', 'language',
            'subtitles_available', 'content_type', 'creator', 'series_name',
            'episode_number', 'difficulty_level', 'is_live', 'scheduled_live_time',
            'live_stream_url', 'is_liked', 'is_bookmarked', 'user_rating',
            'watch_progress', 'created_at', 'updated_at', 'published_at'
        )
        read_only_fields = (
            'id', 'slug', 'author', 'view_count', 'like_count', 'comment_count',
            'download_count', 'average_rating', 'rating_count', 'duration_formatted',
            'trailer_duration_formatted', 'file_size_formatted', 'is_liked', 
            'is_bookmarked', 'user_rating', 'watch_progress', 'created_at', 
            'updated_at', 'published_at'
        )

class FilmListSerializer(BaseMediaSerializer):
    """Serializer for film list view (minimal data)"""
    
    class Meta:
        model = Film
        fields = (
            'id', 'title', 'slug', 'short_description', 'category', 'tags',
            'thumbnail', 'poster', 'author', 'status', 'is_featured', 'is_trending',
            'is_premium', 'view_count', 'like_count', 'comment_count', 'average_rating',
            'rating_count', 'duration', 'duration_formatted', 'video_quality',
            'release_year', 'mpaa_rating', 'director', 'is_liked', 'is_bookmarked',
            'user_rating', 'watch_progress', 'created_at', 'published_at'
        )
        read_only_fields = (
            'id', 'slug', 'author', 'view_count', 'like_count', 'comment_count',
            'average_rating', 'rating_count', 'created_at', 'published_at'
        )

class FilmDetailSerializer(BaseMediaSerializer):
    """Serializer for film detail view (full data)"""
    related_films = serializers.SerializerMethodField()
    
    class Meta:
        model = Film
        fields = (
            'id', 'title', 'slug', 'description', 'short_description', 'category', 'tags',
            'thumbnail', 'poster', 'banner', 'video_file', 'trailer_file',
            'author', 'status', 'is_featured', 'is_trending', 'is_premium',
            'view_count', 'like_count', 'comment_count', 'download_count',
            'average_rating', 'rating_count', 'duration', 'duration_formatted',
            'trailer_duration', 'trailer_duration_formatted', 'video_quality',
            'file_size', 'file_size_formatted', 'release_year', 'language',
            'subtitles_available', 'director', 'cast', 'producer', 'studio',
            'budget', 'box_office', 'mpaa_rating', 'is_series', 'series_name',
            'episode_number', 'season_number', 'is_liked', 'is_bookmarked',
            'user_rating', 'watch_progress', 'related_films', 'created_at', 'updated_at', 'published_at'
        )
        read_only_fields = (
            'id', 'slug', 'author', 'view_count', 'like_count', 'comment_count',
            'download_count', 'average_rating', 'rating_count', 'created_at',
            'updated_at', 'published_at'
        )
    
    def get_related_films(self, obj):
        """Get related films based on category, director, or genre"""
        related_films = Film.objects.filter(
            category=obj.category,
            status='published'
        ).exclude(id=obj.id)[:5]
        
        return FilmListSerializer(
            related_films, 
            many=True, 
            context=self.context
        ).data

class FilmCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating films"""
    
    class Meta:
        model = Film
        fields = (
            'title', 'description', 'short_description', 'category', 'tags',
            'thumbnail', 'poster', 'banner', 'video_file', 'trailer_file',
            'duration', 'trailer_duration', 'video_quality', 'file_size',
            'status', 'is_featured', 'is_trending', 'is_premium', 'release_year',
            'language', 'subtitles_available', 'director', 'cast', 'producer',
            'studio', 'budget', 'box_office', 'mpaa_rating', 'is_series',
            'series_name', 'episode_number', 'season_number'
        )
    
    def validate_title(self, value):
        """Validate film title"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Title must be at least 2 characters long.")
        return value.strip()
    
    def validate_description(self, value):
        """Validate film description"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters long.")
        return value.strip()
    
    def validate_tags(self, value):
        """Ensure tags is a list of strings"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Tags must be a list.")
        
        if len(value) > 15:
            raise serializers.ValidationError("Maximum 15 tags allowed.")
        
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
    
    def validate_cast(self, value):
        """Ensure cast is a list of strings"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Cast must be a list.")
        
        for member in value:
            if not isinstance(member, str):
                raise serializers.ValidationError("Each cast member must be a string.")
        
        return value
    
    def validate_subtitles_available(self, value):
        """Ensure subtitles_available is a list of language codes"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Subtitles available must be a list.")
        
        return value
    
    def validate_duration(self, value):
        """Validate duration is positive"""
        if value is not None and value <= 0:
            raise serializers.ValidationError("Duration must be positive.")
        return value
    
    def create(self, validated_data):
        """Create film with author"""
        validated_data['author'] = self.context['request'].user
        
        # Set published_at if status is published
        if validated_data.get('status') == 'published':
            validated_data['published_at'] = timezone.now()
        
        return Film.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """Update film"""
        # Update published_at if status changes to published
        if (validated_data.get('status') == 'published' and 
            instance.status != 'published'):
            validated_data['published_at'] = timezone.now()
        
        # Update film fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance

class ContentListSerializer(BaseMediaSerializer):
    """Serializer for content list view (minimal data)"""
    
    class Meta:
        model = Content
        fields = (
            'id', 'title', 'slug', 'short_description', 'category', 'tags',
            'thumbnail', 'poster', 'author', 'status', 'is_featured', 'is_trending',
            'is_premium', 'view_count', 'like_count', 'comment_count', 'average_rating',
            'rating_count', 'duration', 'duration_formatted', 'video_quality',
            'content_type', 'creator', 'series_name', 'difficulty_level',
            'is_live', 'is_liked', 'is_bookmarked', 'user_rating', 'watch_progress',
            'created_at', 'published_at'
        )
        read_only_fields = (
            'id', 'slug', 'author', 'view_count', 'like_count', 'comment_count',
            'average_rating', 'rating_count', 'created_at', 'published_at'
        )

class ContentDetailSerializer(BaseMediaSerializer):
    """Serializer for content detail view (full data)"""
    related_content = serializers.SerializerMethodField()
    
    class Meta:
        model = Content
        fields = (
            'id', 'title', 'slug', 'description', 'short_description', 'category', 'tags',
            'thumbnail', 'poster', 'banner', 'video_file', 'trailer_file',
            'author', 'status', 'is_featured', 'is_trending', 'is_premium',
            'view_count', 'like_count', 'comment_count', 'download_count',
            'average_rating', 'rating_count', 'duration', 'duration_formatted',
            'trailer_duration', 'trailer_duration_formatted', 'video_quality',
            'file_size', 'file_size_formatted', 'release_year', 'language',
            'subtitles_available', 'content_type', 'creator', 'series_name',
            'episode_number', 'difficulty_level', 'is_live', 'scheduled_live_time',
            'live_stream_url', 'is_liked', 'is_bookmarked', 'user_rating',
            'watch_progress', 'related_content', 'created_at', 'updated_at', 'published_at'
        )
        read_only_fields = (
            'id', 'slug', 'author', 'view_count', 'like_count', 'comment_count',
            'download_count', 'average_rating', 'rating_count', 'created_at',
            'updated_at', 'published_at'
        )
    
    def get_related_content(self, obj):
        """Get related content based on category and type"""
        related_content = Content.objects.filter(
            category=obj.category,
            status='published'
        ).exclude(id=obj.id)[:5]
        
        return ContentListSerializer(
            related_content, 
            many=True, 
            context=self.context
        ).data

class ContentCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating content"""
    
    class Meta:
        model = Content
        fields = (
            'title', 'description', 'short_description', 'category', 'tags',
            'thumbnail', 'poster', 'banner', 'video_file', 'trailer_file',
            'duration', 'trailer_duration', 'video_quality', 'file_size',
            'status', 'is_featured', 'is_trending', 'is_premium', 'release_year',
            'language', 'subtitles_available', 'content_type', 'creator',
            'series_name', 'episode_number', 'difficulty_level', 'is_live',
            'scheduled_live_time', 'live_stream_url'
        )
    
    def validate_title(self, value):
        """Validate content title"""
        if len(value.strip()) < 2:
            raise serializers.ValidationError("Title must be at least 2 characters long.")
        return value.strip()
    
    def validate_description(self, value):
        """Validate content description"""
        if len(value.strip()) < 10:
            raise serializers.ValidationError("Description must be at least 10 characters long.")
        return value.strip()
    
    def validate_tags(self, value):
        """Ensure tags is a list of strings"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Tags must be a list.")
        
        if len(value) > 15:
            raise serializers.ValidationError("Maximum 15 tags allowed.")
        
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
    
    def validate_scheduled_live_time(self, value):
        """Validate scheduled live time is in the future"""
        if value and value <= timezone.now():
            raise serializers.ValidationError("Scheduled live time must be in the future.")
        return value
    
    def create(self, validated_data):
        """Create content with author"""
        validated_data['author'] = self.context['request'].user
        
        # Set published_at if status is published
        if validated_data.get('status') == 'published':
            validated_data['published_at'] = timezone.now()
        
        return Content.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """Update content"""
        # Update published_at if status changes to published
        if (validated_data.get('status') == 'published' and 
            instance.status != 'published'):
            validated_data['published_at'] = timezone.now()
        
        # Update content fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance

class MediaInteractionSerializer(serializers.ModelSerializer):
    """Serializer for media interactions (like, bookmark, watch, rate)"""
    
    class Meta:
        model = MediaInteraction
        fields = (
            'id', 'interaction_type', 'watch_progress', 'watch_time',
            'rating', 'created_at'
        )
        read_only_fields = ('id', 'created_at')
    
    def validate(self, attrs):
        """Validate interaction data"""
        interaction_type = attrs.get('interaction_type')
        
        # Rating validation
        if interaction_type == 'rate':
            if 'rating' not in attrs or attrs['rating'] is None:
                raise serializers.ValidationError("Rating is required for rate interaction.")
            if not (1 <= attrs['rating'] <= 5):
                raise serializers.ValidationError("Rating must be between 1 and 5.")
        
        # Watch progress validation
        if interaction_type == 'watch':
            if 'watch_progress' in attrs and attrs['watch_progress'] is not None:
                if not (0 <= attrs['watch_progress'] <= 100):
                    raise serializers.ValidationError("Watch progress must be between 0 and 100.")
        
        return attrs
    
    def create(self, validated_data):
        """Create or update interaction"""
        user = self.context['request'].user
        content_type = self.context['content_type']
        object_id = self.context['object_id']
        interaction_type = validated_data['interaction_type']
        
        # For like and bookmark, toggle the interaction
        if interaction_type in ['like', 'bookmark']:
            interaction, created = MediaInteraction.objects.get_or_create(
                user=user,
                content_type=content_type,
                object_id=object_id,
                interaction_type=interaction_type,
                defaults=validated_data
            )
            
            if not created:
                # If interaction exists, delete it (toggle off)
                interaction.delete()
                return None
            
            return interaction
        
        # For watch and rate interactions, update if exists
        else:
            interaction, created = MediaInteraction.objects.update_or_create(
                user=user,
                content_type=content_type,
                object_id=object_id,
                interaction_type=interaction_type,
                defaults=validated_data
            )
            return interaction

class MediaCollectionSerializer(serializers.ModelSerializer):
    """Serializer for media collections"""
    user = AuthorSerializer(read_only=True)
    films = FilmListSerializer(many=True, read_only=True)
    content = ContentListSerializer(many=True, read_only=True)
    total_items = serializers.IntegerField(read_only=True)
    film_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        help_text="List of film IDs to add to collection"
    )
    content_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        help_text="List of content IDs to add to collection"
    )
    
    class Meta:
        model = MediaCollection
        fields = (
            'id', 'name', 'description', 'user', 'films', 'content',
            'total_items', 'film_ids', 'content_ids', 'is_public',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        """Create collection with media"""
        film_ids = validated_data.pop('film_ids', [])
        content_ids = validated_data.pop('content_ids', [])
        validated_data['user'] = self.context['request'].user
        
        collection = MediaCollection.objects.create(**validated_data)
        
        if film_ids:
            films = Film.objects.filter(id__in=film_ids, status='published')
            collection.films.set(films)
        
        if content_ids:
            content = Content.objects.filter(id__in=content_ids, status='published')
            collection.content.set(content)
        
        return collection
    
    def update(self, instance, validated_data):
        """Update collection and media"""
        film_ids = validated_data.pop('film_ids', None)
        content_ids = validated_data.pop('content_ids', None)
        
        # Update collection fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update media if provided
        if film_ids is not None:
            films = Film.objects.filter(id__in=film_ids, status='published')
            instance.films.set(films)
        
        if content_ids is not None:
            content = Content.objects.filter(id__in=content_ids, status='published')
            instance.content.set(content)
        
        return instance

class PlaylistItemSerializer(serializers.ModelSerializer):
    """Serializer for playlist items"""
    media_details = serializers.SerializerMethodField()
    
    class Meta:
        model = PlaylistItem
        fields = ('id', 'content_type', 'object_id', 'order', 'media_details', 'created_at')
        read_only_fields = ('id', 'created_at')
    
    def get_media_details(self, obj):
        """Get details of the media item"""
        if obj.content_type == 'film':
            try:
                film = Film.objects.get(id=obj.object_id)
                return FilmListSerializer(film, context=self.context).data
            except Film.DoesNotExist:
                return None
        else:
            try:
                content = Content.objects.get(id=obj.object_id)
                return ContentListSerializer(content, context=self.context).data
            except Content.DoesNotExist:
                return None

class PlaylistSerializer(serializers.ModelSerializer):
    """Serializer for playlists"""
    creator = AuthorSerializer(read_only=True)
    items = PlaylistItemSerializer(many=True, read_only=True)
    total_items = serializers.SerializerMethodField()
    total_duration = serializers.SerializerMethodField()
    
    class Meta:
        model = Playlist
        fields = (
            'id', 'name', 'description', 'creator', 'is_public', 'is_auto_play',
            'thumbnail', 'items', 'total_items', 'total_duration',
            'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'creator', 'created_at', 'updated_at')
    
    def get_total_items(self, obj):
        """Get total number of items in playlist"""
        return obj.items.count()
    
    def get_total_duration(self, obj):
        """Get total duration of all items in playlist"""
        total_seconds = 0
        for item in obj.items.all():
            if item.content_type == 'film':
                try:
                    film = Film.objects.get(id=item.object_id)
                    total_seconds += film.duration
                except Film.DoesNotExist:
                    continue
            else:
                try:
                    content = Content.objects.get(id=item.object_id)
                    total_seconds += content.duration
                except Content.DoesNotExist:
                    continue
        
        # Format as HH:MM:SS
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
    
    def create(self, validated_data):
        """Create playlist"""
        validated_data['creator'] = self.context['request'].user
        return Playlist.objects.create(**validated_data)

class MediaViewSerializer(serializers.ModelSerializer):
    """Serializer for tracking media views"""
    
    class Meta:
        model = MediaView
        fields = (
            'watch_duration', 'completion_percentage', 'quality_watched', 'device_type'
        )
    
    def create(self, validated_data):
        """Create media view with request data"""
        request = self.context['request']
        content_type = self.context['content_type']
        object_id = self.context['object_id']
        
        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        return MediaView.objects.create(
            content_type=content_type,
            object_id=object_id,
            user=request.user if request.user.is_authenticated else None,
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            **validated_data
        )

class MediaStatsSerializer(serializers.Serializer):
    """Serializer for media statistics"""
    total_films = serializers.IntegerField()
    total_content = serializers.IntegerField()
    total_views = serializers.IntegerField()
    total_likes = serializers.IntegerField()
    total_comments = serializers.IntegerField()
    avg_rating = serializers.FloatField()
    trending_films = FilmListSerializer(many=True)
    trending_content = ContentListSerializer(many=True)
    featured_films = FilmListSerializer(many=True)
    featured_content = ContentListSerializer(many=True)
    recent_films = FilmListSerializer(many=True)
    recent_content = ContentListSerializer(many=True)