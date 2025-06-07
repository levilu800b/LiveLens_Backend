# type: ignore

# animations/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import (
    Animation, AnimationInteraction, AnimationView, AnimationCollection,
    AnimationPlaylist, AIAnimationRequest
)

User = get_user_model()

class AuthorSerializer(serializers.ModelSerializer):
    """Serializer for animation author information"""
    full_name = serializers.CharField(read_only=True)
    
    class Meta:
        model = User
        fields = ('id', 'username', 'first_name', 'last_name', 'full_name', 'avatar')
        read_only_fields = ('id', 'username', 'first_name', 'last_name', 'full_name', 'avatar')

class AnimationListSerializer(serializers.ModelSerializer):
    """Serializer for animation list view (minimal data)"""
    author = AuthorSerializer(read_only=True)
    duration_formatted = serializers.CharField(read_only=True)
    trailer_duration_formatted = serializers.CharField(read_only=True)
    file_size_formatted = serializers.CharField(read_only=True)
    resolution_formatted = serializers.CharField(read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()
    watch_progress = serializers.SerializerMethodField()
    
    class Meta:
        model = Animation
        fields = (
            'id', 'title', 'slug', 'short_description', 'category', 'animation_type',
            'tags', 'thumbnail', 'poster', 'author', 'status', 'is_featured',
            'is_trending', 'is_premium', 'is_ai_generated', 'view_count', 'like_count',
            'comment_count', 'average_rating', 'rating_count', 'duration',
            'duration_formatted', 'trailer_duration_formatted', 'video_quality',
            'frame_rate', 'file_size_formatted', 'resolution_formatted',
            'is_series', 'series_name', 'episode_number', 'season_number',
            'is_liked', 'is_bookmarked', 'user_rating', 'watch_progress',
            'created_at', 'published_at'
        )
        read_only_fields = (
            'id', 'slug', 'author', 'view_count', 'like_count', 'comment_count',
            'average_rating', 'rating_count', 'created_at', 'published_at'
        )
    
    def get_is_liked(self, obj):
        """Check if current user has liked this animation"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return AnimationInteraction.objects.filter(
                user=request.user,
                animation=obj,
                interaction_type='like'
            ).exists()
        return False
    
    def get_is_bookmarked(self, obj):
        """Check if current user has bookmarked this animation"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return AnimationInteraction.objects.filter(
                user=request.user,
                animation=obj,
                interaction_type='bookmark'
            ).exists()
        return False
    
    def get_user_rating(self, obj):
        """Get current user's rating for this animation"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                interaction = AnimationInteraction.objects.get(
                    user=request.user,
                    animation=obj,
                    interaction_type='rate'
                )
                return interaction.rating
            except AnimationInteraction.DoesNotExist:
                pass
        return None
    
    def get_watch_progress(self, obj):
        """Get user's watching progress for this animation"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                interaction = AnimationInteraction.objects.get(
                    user=request.user,
                    animation=obj,
                    interaction_type='watch'
                )
                return {
                    'progress_percentage': interaction.watch_progress,
                    'watch_time': interaction.watch_time
                }
            except AnimationInteraction.DoesNotExist:
                pass
        return None

class AnimationDetailSerializer(serializers.ModelSerializer):
    """Serializer for animation detail view (full data)"""
    author = AuthorSerializer(read_only=True)
    duration_formatted = serializers.CharField(read_only=True)
    trailer_duration_formatted = serializers.CharField(read_only=True)
    file_size_formatted = serializers.CharField(read_only=True)
    resolution_formatted = serializers.CharField(read_only=True)
    is_liked = serializers.SerializerMethodField()
    is_bookmarked = serializers.SerializerMethodField()
    user_rating = serializers.SerializerMethodField()
    watch_progress = serializers.SerializerMethodField()
    next_episode = serializers.SerializerMethodField()
    previous_episode = serializers.SerializerMethodField()
    related_animations = serializers.SerializerMethodField()
    
    class Meta:
        model = Animation
        fields = (
            'id', 'title', 'slug', 'description', 'short_description', 'category',
            'animation_type', 'tags', 'thumbnail', 'poster', 'banner', 'video_file',
            'trailer_file', 'project_file', 'storyboard', 'concept_art', 'author',
            'status', 'is_featured', 'is_trending', 'is_premium', 'is_series',
            'series_name', 'episode_number', 'season_number', 'is_ai_generated',
            'ai_prompt', 'ai_model_used', 'generation_parameters', 'view_count',
            'like_count', 'comment_count', 'download_count', 'share_count',
            'average_rating', 'rating_count', 'duration', 'duration_formatted',
            'trailer_duration', 'trailer_duration_formatted', 'video_quality',
            'frame_rate', 'file_size', 'file_size_formatted', 'resolution_width',
            'resolution_height', 'resolution_formatted', 'animation_software',
            'render_engine', 'production_time', 'release_year', 'language',
            'subtitles_available', 'director', 'animator', 'voice_actors',
            'music_composer', 'sound_designer', 'studio', 'budget',
            'is_liked', 'is_bookmarked', 'user_rating', 'watch_progress',
            'next_episode', 'previous_episode', 'related_animations',
            'created_at', 'updated_at', 'published_at'
        )
        read_only_fields = (
            'id', 'slug', 'author', 'view_count', 'like_count', 'comment_count',
            'download_count', 'share_count', 'average_rating', 'rating_count',
            'created_at', 'updated_at', 'published_at'
        )
    
    def get_is_liked(self, obj):
        """Check if current user has liked this animation"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return AnimationInteraction.objects.filter(
                user=request.user,
                animation=obj,
                interaction_type='like'
            ).exists()
        return False
    
    def get_is_bookmarked(self, obj):
        """Check if current user has bookmarked this animation"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return AnimationInteraction.objects.filter(
                user=request.user,
                animation=obj,
                interaction_type='bookmark'
            ).exists()
        return False
    
    def get_user_rating(self, obj):
        """Get current user's rating for this animation"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                interaction = AnimationInteraction.objects.get(
                    user=request.user,
                    animation=obj,
                    interaction_type='rate'
                )
                return interaction.rating
            except AnimationInteraction.DoesNotExist:
                pass
        return None
    
    def get_watch_progress(self, obj):
        """Get user's watching progress for this animation"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            try:
                interaction = AnimationInteraction.objects.get(
                    user=request.user,
                    animation=obj,
                    interaction_type='watch'
                )
                return {
                    'progress_percentage': interaction.watch_progress,
                    'watch_time': interaction.watch_time
                }
            except AnimationInteraction.DoesNotExist:
                pass
        return None
    
    def get_next_episode(self, obj):
        """Get next episode in series"""
        if obj.is_series and obj.episode_number:
            next_ep = Animation.objects.filter(
                series_name=obj.series_name,
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
        if obj.is_series and obj.episode_number:
            prev_ep = Animation.objects.filter(
                series_name=obj.series_name,
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
    
    def get_related_animations(self, obj):
        """Get related animations by category or tags"""
        related = Animation.objects.filter(
            status='published',
            category=obj.category
        ).exclude(id=obj.id)[:5]
        
        return AnimationListSerializer(related, many=True, context=self.context).data

class AnimationCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating and updating animations"""
    
    class Meta:
        model = Animation
        fields = (
            'title', 'description', 'short_description', 'category', 'animation_type',
            'tags', 'thumbnail', 'poster', 'banner', 'video_file', 'trailer_file',
            'project_file', 'storyboard', 'concept_art', 'duration', 'trailer_duration',
            'video_quality', 'frame_rate', 'file_size', 'resolution_width',
            'resolution_height', 'animation_software', 'render_engine', 'production_time',
            'status', 'is_featured', 'is_trending', 'is_premium', 'is_series',
            'series_name', 'episode_number', 'season_number', 'is_ai_generated',
            'ai_prompt', 'ai_model_used', 'generation_parameters', 'release_year',
            'language', 'subtitles_available', 'director', 'animator', 'voice_actors',
            'music_composer', 'sound_designer', 'studio', 'budget'
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
    
    def validate_voice_actors(self, value):
        """Ensure voice_actors is a list of strings"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Voice actors must be a list.")
        
        for actor in value:
            if not isinstance(actor, str):
                raise serializers.ValidationError("Each voice actor must be a string.")
        
        return value
    
    def validate_subtitles_available(self, value):
        """Ensure subtitles_available is a list of language codes"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Subtitles available must be a list.")
        
        return value
    
    def validate(self, attrs):
        """Validate animation data"""
        # Series validation
        if attrs.get('is_series'):
            if not attrs.get('series_name'):
                raise serializers.ValidationError("Series name is required for series animations.")
            if not attrs.get('episode_number'):
                raise serializers.ValidationError("Episode number is required for series animations.")
        
        # AI generation validation
        if attrs.get('is_ai_generated') and not attrs.get('ai_prompt'):
            raise serializers.ValidationError("AI prompt is required for AI-generated animations.")
        
        return attrs
    
    def create(self, validated_data):
        """Create animation with author"""
        validated_data['author'] = self.context['request'].user
        
        # Set published_at if status is published
        if validated_data.get('status') == 'published':
            validated_data['published_at'] = timezone.now()
        
        return Animation.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        """Update animation"""
        # Update published_at if status changes to published
        if (validated_data.get('status') == 'published' and 
            instance.status != 'published'):
            validated_data['published_at'] = timezone.now()
        
        # Update animation fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        return instance

class AnimationInteractionSerializer(serializers.ModelSerializer):
    """Serializer for animation interactions (like, bookmark, watch, rate)"""
    
    class Meta:
        model = AnimationInteraction
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
        animation = self.context['animation']
        interaction_type = validated_data['interaction_type']
        
        # For like and bookmark, toggle the interaction
        if interaction_type in ['like', 'bookmark']:
            interaction, created = AnimationInteraction.objects.get_or_create(
                user=user,
                animation=animation,
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
            interaction, created = AnimationInteraction.objects.update_or_create(
                user=user,
                animation=animation,
                interaction_type=interaction_type,
                defaults=validated_data
            )
            return interaction

class AnimationCollectionSerializer(serializers.ModelSerializer):
    """Serializer for animation collections"""
    user = AuthorSerializer(read_only=True)
    animations = AnimationListSerializer(many=True, read_only=True)
    animation_count = serializers.IntegerField(read_only=True)
    animation_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        help_text="List of animation IDs to add to collection"
    )
    
    class Meta:
        model = AnimationCollection
        fields = (
            'id', 'name', 'description', 'user', 'animations', 'animation_count',
            'animation_ids', 'is_public', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'user', 'created_at', 'updated_at')
    
    def create(self, validated_data):
        """Create collection with animations"""
        animation_ids = validated_data.pop('animation_ids', [])
        validated_data['user'] = self.context['request'].user
        
        collection = AnimationCollection.objects.create(**validated_data)
        
        if animation_ids:
            animations = Animation.objects.filter(id__in=animation_ids, status='published')
            collection.animations.set(animations)
        
        return collection
    
    def update(self, instance, validated_data):
        """Update collection and animations"""
        animation_ids = validated_data.pop('animation_ids', None)
        
        # Update collection fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update animations if provided
        if animation_ids is not None:
            animations = Animation.objects.filter(id__in=animation_ids, status='published')
            instance.animations.set(animations)
        
        return instance

class AnimationPlaylistSerializer(serializers.ModelSerializer):
    """Serializer for animation playlists"""
    creator = AuthorSerializer(read_only=True)
    animations = AnimationListSerializer(many=True, read_only=True)
    animation_count = serializers.IntegerField(read_only=True)
    total_duration = serializers.IntegerField(read_only=True)
    total_duration_formatted = serializers.SerializerMethodField()
    animation_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
        help_text="List of animation IDs to add to playlist"
    )
    
    class Meta:
        model = AnimationPlaylist
        fields = (
            'id', 'name', 'description', 'creator', 'animations', 'animation_count',
            'total_duration', 'total_duration_formatted', 'animation_ids',
            'is_public', 'is_auto_play', 'thumbnail', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'creator', 'created_at', 'updated_at')
    
    def get_total_duration_formatted(self, obj):
        """Get total duration in HH:MM:SS format"""
        total_seconds = obj.total_duration
        if total_seconds:
            hours, remainder = divmod(total_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        return "00:00:00"
    
    def create(self, validated_data):
        """Create playlist with animations"""
        animation_ids = validated_data.pop('animation_ids', [])
        validated_data['creator'] = self.context['request'].user
        
        playlist = AnimationPlaylist.objects.create(**validated_data)
        
        if animation_ids:
            animations = Animation.objects.filter(id__in=animation_ids, status='published')
            playlist.animations.set(animations)
        
        return playlist
    
    def update(self, instance, validated_data):
        """Update playlist and animations"""
        animation_ids = validated_data.pop('animation_ids', None)
        
        # Update playlist fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update animations if provided
        if animation_ids is not None:
            animations = Animation.objects.filter(id__in=animation_ids, status='published')
            instance.animations.set(animations)
        
        return instance

class AnimationViewSerializer(serializers.ModelSerializer):
    """Serializer for tracking animation views"""
    
    class Meta:
        model = AnimationView
        fields = (
            'watch_duration', 'completion_percentage', 'quality_watched', 'device_type'
        )
    
    def create(self, validated_data):
        """Create animation view with request data"""
        request = self.context['request']
        animation = self.context['animation']
        
        # Get IP address
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0]
        else:
            ip_address = request.META.get('REMOTE_ADDR')
        
        return AnimationView.objects.create(
            animation=animation,
            user=request.user if request.user.is_authenticated else None,
            ip_address=ip_address,
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
            **validated_data
        )

class AIAnimationRequestSerializer(serializers.ModelSerializer):
    """Serializer for AI animation generation requests"""
    user = AuthorSerializer(read_only=True)
    animation = AnimationListSerializer(read_only=True)
    
    class Meta:
        model = AIAnimationRequest
        fields = (
            'id', 'user', 'animation', 'prompt', 'style', 'duration_requested',
            'quality_requested', 'frame_rate_requested', 'status', 'ai_model_used',
            'processing_time', 'error_message', 'additional_parameters',
            'created_at', 'updated_at', 'completed_at'
        )
        read_only_fields = (
            'id', 'user', 'animation', 'status', 'ai_model_used', 'processing_time',
            'error_message', 'created_at', 'updated_at', 'completed_at'
        )
    
    def create(self, validated_data):
        """Create AI animation request"""
        validated_data['user'] = self.context['request'].user
        return AIAnimationRequest.objects.create(**validated_data)

class AnimationStatsSerializer(serializers.Serializer):
    """Serializer for animation statistics"""
    total_animations = serializers.IntegerField()
    published_animations = serializers.IntegerField()
    ai_generated_animations = serializers.IntegerField()
    total_views = serializers.IntegerField()
    total_likes = serializers.IntegerField()
    trending_animations = AnimationListSerializer(many=True)
    featured_animations = AnimationListSerializer(many=True)
    recent_animations = AnimationListSerializer(many=True)
    top_categories = serializers.ListField()
    ai_requests_pending = serializers.IntegerField()