# type: ignore

# podcasts/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import (
    PodcastSeries, Podcast, PodcastInteraction, PodcastPlaylist,
    PodcastSubscription, PodcastView
)

User = get_user_model()

class AuthorSerializer(serializers.ModelSerializer):
    """Serializer for podcast author information"""
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'full_name', 'avatar')
        read_only_fields = ('id', 'username', 'first_name', 'last_name', 'full_name', 'avatar')

class PodcastSeriesListSerializer(serializers.ModelSerializer):
    """Serializer for podcast series list view (minimal data)"""
    author = AuthorSerializer(read_only=True)
    episode_count = serializers.IntegerField(read_only=True)
    latest_episode = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    
    class Meta:
        model = PodcastSeries
        fields = (
            'id', 'title', 'slug', 'short_description', 'category', 'tags',
            'cover_image', 'thumbnail', 'author', 'host', 'language',
            'is_featured', 'is_explicit', 'episode_count', 'latest_episode',
            'is_subscribed', 'created_at'
        )
        read_only_fields = (
            'id', 'slug', 'author', 'episode_count', 'created_at'
        )
    
    def get_latest_episode(self, obj):
        """Get latest episode info"""
        latest = obj.latest_episode
        if latest:
            return {
                'id': latest.id,
                'title': latest.title,
                'episode_number': latest.episode_number,
                'published_at': latest.published_at
            }
        return None
    
    def get_is_subscribed(self, obj):
        """Check if current user is subscribed to this series"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PodcastSubscription.objects.filter(
                user=request.user,
                series=obj
            ).exists()
        return False

class PodcastSeriesDetailSerializer(serializers.ModelSerializer):
    """Serializer for podcast series detail view (full data)"""
    author = AuthorSerializer(read_only=True)
    episode_count = serializers.IntegerField(read_only=True)
    total_duration = serializers.IntegerField(read_only=True)
    latest_episode = serializers.SerializerMethodField()
    recent_episodes = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()
    subscriber_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PodcastSeries
        fields = (
            'id', 'title', 'slug', 'description', 'short_description', 
            'category', 'subcategory', 'tags', 'cover_image', 'thumbnail', 
            'banner', 'author', 'host', 'language', 'is_active', 'is_featured',
            'is_explicit', 'website', 'rss_feed', 'episode_count', 'total_duration',
            'latest_episode', 'recent_episodes', 'is_subscribed', 'subscriber_count',
            'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'slug', 'author', 'episode_count', 'total_duration',
            'created_at', 'updated_at'
        )
    
    def get_latest_episode(self, obj):
        """Get latest episode detailed info"""
        latest = obj.latest_episode
        if latest:
            from .serializers import PodcastListSerializer
            return PodcastListSerializer(latest, context=self.context).data
        return None
    
    def get_recent_episodes(self, obj):
        """Get recent episodes (last 5)"""
        episodes = obj.episodes.filter(status='published').order_by('-published_at')[:5]
        from .serializers import PodcastListSerializer
        return PodcastListSerializer(episodes, many=True, context=self.context).data
    
    def get_is_subscribed(self, obj):
        """Check if current user is subscribed to this series"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PodcastSubscription.objects.filter(
                user=request.user,
                series=obj
            ).exists()
        return False
    
    def get_subscriber_count(self, obj):
        """Get total subscriber count"""
        return obj.subscribers.count()

class PodcastSeriesCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating podcast series"""
    
    class Meta:
        model = PodcastSeries
        fields = (
            'title', 'description', 'short_description', 'category', 'subcategory',
            'tags', 'cover_image', 'thumbnail', 'banner', 'host', 'language',
            'is_active', 'is_featured', 'is_explicit', 'website', 'rss_feed'
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
        """Create series with author"""
        validated_data['author'] = self.context['request'].user
        return PodcastSeries.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """Update series"""
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance

class PodcastListSerializer(serializers.ModelSerializer):
    """Serializer for podcast episode list view (minimal data)"""
    author = AuthorSerializer(read_only=True)
    series = PodcastSeriesListSerializer(read_only=True)
    duration_formatted = serializers.CharField(read_only=True)
    file_size_formatted = serializers.CharField(read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()
    listen_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Podcast
        fields = (
            'id', 'title', 'slug', 'summary', 'series', 'episode_number',
            'season_number', 'episode_type', 'cover_image', 'thumbnail',
            'author', 'guest', 'tags', 'status', 'is_featured', 'is_premium',
            'is_explicit', 'play_count', 'like_count', 'comment_count',
            'average_rating', 'rating_count', 'duration', 'duration_formatted',
            'file_size_formatted', 'audio_quality', 'is_liked', 'is_bookmarked',
            'user_rating', 'listen_progress', 'created_at', 'published_at'
        )
        read_only_fields = (
            'id', 'slug', 'author', 'play_count', 'like_count', 'comment_count',
            'average_rating', 'rating_count', 'created_at', 'published_at'
        )
    
    def get_is_liked(self, obj):
        """Check if current user has liked this episode"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PodcastInteraction.objects.filter(
                user=request.user,
                podcast=obj,
                interaction_type='like'
            ).exists()
        return False
    
    def get_is_bookmarked(self, obj):
        """Check if current user has bookmarked this episode"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PodcastInteraction.objects.filter(
                user=request.user,
                podcast=obj,
                interaction_type='bookmark'
            ).exists()
        return False
    
    def get_user_rating(self, obj):
        """Get current user's rating for this episode"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                interaction = PodcastInteraction.objects.get(
                    user=request.user,
                    podcast=obj,
                    interaction_type='rate'
                )
                return interaction.rating
            except PodcastInteraction.DoesNotExist:
                pass
        return None
    
    def get_listen_progress(self, obj):
        """Get user's listening progress for this episode"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                interaction = PodcastInteraction.objects.get(
                    user=request.user,
                    podcast=obj,
                    interaction_type='listen'
                )
                return {
                    'progress_percentage': interaction.listen_progress,
                    'listen_time': interaction.listen_time
                }
            except PodcastInteraction.DoesNotExist:
                pass
        return None

class PodcastDetailSerializer(serializers.ModelSerializer):
    """Serializer for podcast episode detail view (full data)"""
    author = AuthorSerializer(read_only=True)
    series = PodcastSeriesListSerializer(read_only=True)
    duration_formatted = serializers.CharField(read_only=True)
    file_size_formatted = serializers.CharField(read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()
    listen_progress = serializers.SerializerMethodField()
    next_episode = serializers.SerializerMethodField()
    previous_episode = serializers.SerializerMethodField()
    
    class Meta:
        model = Podcast
        fields = (
            'id', 'title', 'slug', 'description', 'summary', 'series',
            'episode_number', 'season_number', 'episode_type', 'audio_file',
            'video_file', 'transcript_file', 'cover_image', 'thumbnail',
            'author', 'guest', 'tags', 'status', 'is_featured', 'is_premium',
            'is_explicit', 'play_count', 'like_count', 'comment_count',
            'download_count', 'average_rating', 'rating_count', 'duration',
            'duration_formatted', 'file_size', 'file_size_formatted',
            'audio_quality', 'external_url', 'is_liked', 'is_bookmarked',
            'user_rating', 'listen_progress', 'next_episode', 'previous_episode',
            'created_at', 'updated_at', 'published_at', 'scheduled_at'
        )
        read_only_fields = (
            'id', 'slug', 'author', 'play_count', 'like_count', 'comment_count',
            'download_count', 'average_rating', 'rating_count', 'created_at',
            'updated_at', 'published_at'
        )
    
    def get_is_liked(self, obj):
        """Check if current user has liked this episode"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PodcastInteraction.objects.filter(
                user=request.user,
                podcast=obj,
                interaction_type='like'
            ).exists()
        return False
    
    def get_is_bookmarked(self, obj):
        """Check if current user has bookmarked this episode"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return PodcastInteraction.objects.filter(
                user=request.user,
                podcast=obj,
                interaction_type='bookmark'
            ).exists()
        return False
    
    def get_user_rating(self, obj):
        """Get current user's rating for this episode"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                interaction = PodcastInteraction.objects.get(
                    user=request.user,
                    podcast=obj,
                    interaction_type='rate'
                )
                return interaction.rating
            except PodcastInteraction.DoesNotExist:
                pass
        return None
    
    def get_listen_progress(self, obj):
        """Get user's listening progress for this episode"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                interaction = PodcastInteraction.objects.get(
                    user=request.user,
                    podcast=obj,
                    interaction_type='listen'
                )
                return {
                    'progress_percentage': interaction.listen_progress,
                    'listen_time': interaction.listen_time
                }
            except PodcastInteraction.DoesNotExist:
                pass
        return None
    
    def get_next_episode(self, obj):
        """Get next episode in series"""
        next_ep = Podcast.objects.filter(
            series=obj.series,
            season_number=obj.season_number,
            episode_number__gt=obj.episode_number,
            status='published'
        ).order_by('episode_number').first()
        
        if next_ep:
            return {
                'id': next_ep.id,
                'title': next_ep.title,
                'episode_number': next_ep.episode_number,
                'slug': next_ep.slug
            }
        return None
    
    def get_previous_episode(self, obj):
        """Get previous episode in series"""
        prev_ep = Podcast.objects.filter(
            series=obj.series,
            season_number=obj.season_number,
            episode_number__lt=obj.episode_number,
            status='published'
        ).order_by('-episode_number').first()
        
        if prev_ep:
            return {
                'id': prev_ep.id,
                'title': prev_ep.title,
                'episode_number': prev_ep.episode_number,
                'slug': prev_ep.slug
            }
        return None

class PodcastCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating podcast episodes"""
    
    class Meta:
        model = Podcast
        fields = (
            'title', 'description', 'summary', 'series', 'episode_number',
            'season_number', 'episode_type', 'audio_file', 'video_file',
            'transcript_file', 'cover_image', 'thumbnail', 'guest', 'tags',
            'status', 'is_featured', 'is_premium', 'is_explicit', 'duration',
            'file_size', 'audio_quality', 'external_url', 'scheduled_at'
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
    
    def validate(self, attrs):
        """Validate episode data"""
        series = attrs.get('series')
        episode_number = attrs.get('episode_number')
        season_number = attrs.get('season_number', 1)
        
        # Check for duplicate episode numbers within series/season
        if series and episode_number:
            existing = Podcast.objects.filter(
                series=series,
                season_number=season_number,
                episode_number=episode_number
            )
            
            # Exclude current instance if updating
            if self.instance:
                existing = existing.exclude(pk=self.instance.pk)
            
            if existing.exists():
                raise serializers.ValidationError(
                    f"Episode {episode_number} already exists in season {season_number} of this series."
                )
        
        return attrs
    
    def create(self, validated_data):
        """Create episode with author"""
        validated_data['author'] = self.context['request'].user
        
        # Set published_at if status is published
        if validated_data.get('status') == 'published':
            validated_data['published_at'] = timezone.now()
        
        return Podcast.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """Update episode"""
        # Update published_at if status changes to published
        if (validated_data.get('status') == 'published' and 
            instance.status != 'published'):
            validated_data['published_at'] = timezone.now()
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance

class PodcastInteractionSerializer(serializers.ModelSerializer):
    """Serializer for podcast interactions (like, bookmark, listen, rate)"""
    
    class Meta:
        model = PodcastInteraction
        fields = (
            'id', 'interaction_type', 'listen_progress', 'listen_time',
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
        
        # Listen progress validation
        if interaction_type == 'listen':
            if 'listen_progress' in attrs and attrs['listen_progress'] is not None:
                if not (0 <= attrs['listen_progress'] <= 100):
                    raise serializers.ValidationError("Listen progress must be between 0 and 100.")
        
        return attrs
    
    def create(self, validated_data):
        """Create or update interaction"""
        user = self.context['request'].user
        podcast = self.context.get('podcast')
        series = self.context.get('series')
        interaction_type = validated_data['interaction_type']
        
        # For like and bookmark, toggle the interaction
        if interaction_type in ['like', 'bookmark']:
            interaction, created = PodcastInteraction.objects.get_or_create(
                user=user,
                podcast=podcast,
                series=series,
                interaction_type=interaction_type,
                defaults=validated_data
            )
            
            if not created:
                # If interaction exists, delete it (toggle off)
                interaction.delete()
                return None
            
            return interaction
        
        # For listen and rate interactions, update if exists
        else:
            interaction, created = PodcastInteraction.objects.update_or_create(
                user=user,
                podcast=podcast,
                series=series,
                interaction_type=interaction_type,
                defaults=validated_data
            )
            return interaction

class PodcastPlaylistSerializer(serializers.ModelSerializer):
    """Serializer for podcast playlists"""
    user = AuthorSerializer(read_only=True)
    episodes = PodcastListSerializer(many=True, read_only=True)
    episode_count = serializers.IntegerField(read_only=True)
    total_duration = serializers.IntegerField(read_only=True)
    episode_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        help_text="List of episode IDs to add to playlist"
    )
    
    class Meta:
        model = PodcastPlaylist
        fields = (
            'id', 'name', 'description', 'user', 'episodes', 'episode_count',
            'total_duration', 'episode_ids', 'is_public', 'auto_play', 'shuffle',
            'cover_image', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        """Create playlist with episodes"""
        episode_ids = validated_data.pop('episode_ids', [])
        validated_data['user'] = self.context['request'].user
        
        playlist = PodcastPlaylist.objects.create(**validated_data)
        
        if episode_ids:
            episodes = Podcast.objects.filter(id__in=episode_ids, status='published')
            playlist.episodes.set(episodes)
        
        return playlist
    
    def update(self, instance, validated_data):
        """Update playlist and episodes"""
        episode_ids = validated_data.pop('episode_ids', None)
        
        # Update playlist fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update episodes if provided
        if episode_ids is not None:
            episodes = Podcast.objects.filter(id__in=episode_ids, status='published')
            instance.episodes.set(episodes)
        
        return instance

class PodcastSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for podcast subscriptions"""
    user = AuthorSerializer(read_only=True)
    series = PodcastSeriesListSerializer(read_only=True)
    
    class Meta:
        model = PodcastSubscription
        fields = (
            'id', 'user', 'series', 'notifications_enabled', 'auto_download',
            'created_at'
        )
        read_only_fields = ('id', 'user', 'series', 'created_at')
    
    def create(self, validated_data):
        """Create subscription"""
        validated_data['user'] = self.context['request'].user
        validated_data['series'] = self.context['series']
        return PodcastSubscription.objects.create(**validated_data)

class PodcastViewSerializer(serializers.ModelSerializer):
    """Serializer for tracking podcast listening"""
    
    class Meta:
        model = PodcastView
        fields = (
            'listen_duration', 'completion_percentage', 'device_type'
        )
    
    def create(self, validated_data):
        """Create podcast view with request data"""
        request = self.context['request']
        podcast = self.context['podcast']
        
        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        return PodcastView.objects.create(
            podcast=podcast,
            user=request.user if request.user.is_authenticated else None,
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            **validated_data
        )
        
# Add this class at the end of podcasts/serializers.py

class PodcastSerializer(serializers.ModelSerializer):
    """General serializer for podcasts - for backward compatibility"""
    author = AuthorSerializer(read_only=True)
    series_info = PodcastSeriesListSerializer(source='series', read_only=True)
    duration_formatted = serializers.CharField(read_only=True)
    file_size_formatted = serializers.CharField(read_only=True)
    
    class Meta:
        model = Podcast
        fields = (
            'id', 'title', 'slug', 'description', 'summary', 'series', 'series_info',
            'episode_number', 'season_number', 'episode_type', 'audio_file', 
            'video_file', 'transcript_file', 'cover_image', 'thumbnail', 'author',
            'host', 'guest', 'tags', 'status', 'is_featured', 'is_premium',
            'is_explicit', 'view_count', 'like_count', 'comment_count',
            'download_count', 'average_rating', 'rating_count', 'duration',
            'duration_formatted', 'file_size', 'file_size_formatted',
            'audio_quality', 'external_url', 'scheduled_at', 'created_at',
            'updated_at', 'published_at'
        )
        read_only_fields = (
            'id', 'slug', 'author', 'view_count', 'like_count', 'comment_count',
            'download_count', 'average_rating', 'rating_count', 'duration_formatted',
            'file_size_formatted', 'created_at', 'updated_at', 'published_at'
        )

class PodcastStatsSerializer(serializers.Serializer):
    """Serializer for podcast statistics"""
    total_series = serializers.IntegerField()
    total_episodes = serializers.IntegerField()
    total_plays = serializers.IntegerField()
    total_subscribers = serializers.IntegerField()
    featured_series = PodcastSeriesListSerializer(many=True)
    trending_episodes = PodcastListSerializer(many=True)
    recent_episodes = PodcastListSerializer(many=True)
    top_series = PodcastSeriesListSerializer(many=True)