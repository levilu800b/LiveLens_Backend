# type: ignore

# animations/filters.py
import django_filters
from django.db.models import Q
from .models import Animation

class AnimationFilter(django_filters.FilterSet):
    """
    Filter for Animation model with comprehensive filtering options
    """
    # Text search
    search = django_filters.CharFilter(method='filter_search', help_text="Search in title, description, director, animator")
    
    # Category filter
    category = django_filters.ChoiceFilter(choices=Animation.CATEGORY_CHOICES)
    
    # Animation type filter
    animation_type = django_filters.ChoiceFilter(choices=Animation.ANIMATION_TYPE_CHOICES)
    
    # Status filter
    status = django_filters.ChoiceFilter(choices=Animation.STATUS_CHOICES)
    
    # Author filter
    author = django_filters.CharFilter(method='filter_author', help_text="Filter by author username or name")
    author_id = django_filters.UUIDFilter(field_name='author__id')
    
    # Boolean filters
    is_featured = django_filters.BooleanFilter()
    is_trending = django_filters.BooleanFilter()
    is_premium = django_filters.BooleanFilter()
    is_series = django_filters.BooleanFilter()
    
    # Date filters
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    published_after = django_filters.DateTimeFilter(field_name='published_at', lookup_expr='gte')
    published_before = django_filters.DateTimeFilter(field_name='published_at', lookup_expr='lte')
    
    # Year filter
    release_year = django_filters.NumberFilter()
    release_year_after = django_filters.NumberFilter(field_name='release_year', lookup_expr='gte')
    release_year_before = django_filters.NumberFilter(field_name='release_year', lookup_expr='lte')
    
    # Numeric filters
    min_view_count = django_filters.NumberFilter(field_name='view_count', lookup_expr='gte')
    max_view_count = django_filters.NumberFilter(field_name='view_count', lookup_expr='lte')
    min_like_count = django_filters.NumberFilter(field_name='like_count', lookup_expr='gte')
    max_like_count = django_filters.NumberFilter(field_name='like_count', lookup_expr='lte')
    min_duration = django_filters.NumberFilter(field_name='duration', lookup_expr='gte')
    max_duration = django_filters.NumberFilter(field_name='duration', lookup_expr='lte')
    min_rating = django_filters.NumberFilter(field_name='average_rating', lookup_expr='gte')
    max_rating = django_filters.NumberFilter(field_name='average_rating', lookup_expr='lte')
    
    # Video quality filter
    video_quality = django_filters.ChoiceFilter(choices=Animation.QUALITY_CHOICES)
    
    # Frame rate filter
    frame_rate = django_filters.ChoiceFilter(choices=Animation.FRAME_RATE_CHOICES)
    
    # Language filter
    language = django_filters.CharFilter(lookup_expr='icontains')
    
    # Director filter
    director = django_filters.CharFilter(lookup_expr='icontains')
    
    # Animator filter
    animator = django_filters.CharFilter(lookup_expr='icontains')
    
    # Studio filter
    studio = django_filters.CharFilter(lookup_expr='icontains')
    
    # Tags filter
    tags = django_filters.CharFilter(method='filter_tags', help_text="Filter by tags (comma-separated)")
    
    # Series filter
    series_name = django_filters.CharFilter(lookup_expr='icontains')
    episode_number = django_filters.NumberFilter()
    season_number = django_filters.NumberFilter()
    
    # Animation software filter
    animation_software = django_filters.CharFilter(lookup_expr='icontains')
    
    # Resolution filters
    min_width = django_filters.NumberFilter(field_name='resolution_width', lookup_expr='gte')
    max_width = django_filters.NumberFilter(field_name='resolution_width', lookup_expr='lte')
    min_height = django_filters.NumberFilter(field_name='resolution_height', lookup_expr='gte')
    max_height = django_filters.NumberFilter(field_name='resolution_height', lookup_expr='lte')
    
    # Production time filter
    min_production_time = django_filters.NumberFilter(field_name='production_time', lookup_expr='gte')
    max_production_time = django_filters.NumberFilter(field_name='production_time', lookup_expr='lte')
    
    # AI model filter
    ai_model_used = django_filters.CharFilter(lookup_expr='icontains')
    
    # Ordering
    ordering = django_filters.OrderingFilter(
        fields=(
            ('created_at', 'created'),
            ('updated_at', 'updated'),
            ('published_at', 'published'),
            ('view_count', 'view_count'),
            ('like_count', 'like_count'),
            ('average_rating', 'rating'),
            ('duration', 'duration'),
            ('release_year', 'release_year'),
            ('production_time', 'production_time'),
            ('title', 'title'),
        ),
        field_labels={
            'created': 'Date Created',
            'updated': 'Date Updated',
            'published': 'Date Published',
            'view_count': 'View Count',
            'like_count': 'Like Count',
            'rating': 'Average Rating',
            'duration': 'Duration',
            'release_year': 'Release Year',
            'production_time': 'Production Time',
            'title': 'Title',
        }
    )
    
    class Meta:
        model = Animation
        fields = [
            'category', 'animation_type', 'status', 'author_id', 'is_featured',
            'is_trending', 'is_premium', 'is_series',
            'release_year', 'video_quality', 'frame_rate', 'language',
            'episode_number', 'season_number'
        ]
    
    def filter_search(self, queryset, name, value):
        """
        Search across multiple fields
        """
        if not value:
            return queryset
        
        return queryset.filter(
            Q(title__icontains=value) |
            Q(description__icontains=value) |
            Q(short_description__icontains=value) |
            Q(director__icontains=value) |
            Q(animator__icontains=value) |
            Q(tags__icontains=value) |
            Q(studio__icontains=value) |
            Q(series_name__icontains=value) |
            Q(animation_software__icontains=value) |
            Q(voice_actors__icontains=value)
        )
    
    def filter_author(self, queryset, name, value):
        """
        Filter by author username or full name
        """
        if not value:
            return queryset
        
        return queryset.filter(
            Q(author__username__icontains=value) |
            Q(author__first_name__icontains=value) |
            Q(author__last_name__icontains=value)
        )
    
    def filter_tags(self, queryset, name, value):
        """
        Filter by tags (comma-separated)
        """
        if not value:
            return queryset
        
        tags = [tag.strip().lower() for tag in value.split(',') if tag.strip()]
        if not tags:
            return queryset
        
        # Filter animations that contain any of the specified tags
        query = Q()
        for tag in tags:
            query |= Q(tags__icontains=tag)
        
        return queryset.filter(query)

class AnimationCollectionFilter(django_filters.FilterSet):
    """
    Filter for AnimationCollection model
    """
    # Text search
    search = django_filters.CharFilter(method='filter_search', help_text="Search in name, description")
    
    # Boolean filters
    is_public = django_filters.BooleanFilter()
    
    # User filter
    user = django_filters.CharFilter(method='filter_user', help_text="Filter by username")
    user_id = django_filters.UUIDFilter(field_name='user__id')
    
    # Date filters
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Animation count filters
    min_animations = django_filters.NumberFilter(method='filter_min_animations')
    max_animations = django_filters.NumberFilter(method='filter_max_animations')
    
    # Ordering
    ordering = django_filters.OrderingFilter(
        fields=(
            ('created_at', 'created'),
            ('updated_at', 'updated'),
            ('name', 'name'),
        )
    )
    
    class Meta:
        model = Animation  # Note: Using Animation model as reference
        fields = ['is_public', 'user_id']
    
    def filter_search(self, queryset, name, value):
        """
        Search across name and description
        """
        if not value:
            return queryset
        
        return queryset.filter(
            Q(name__icontains=value) |
            Q(description__icontains=value)
        )
    
    def filter_user(self, queryset, name, value):
        """
        Filter by username
        """
        if not value:
            return queryset
        
        return queryset.filter(user__username__icontains=value)
    
    def filter_min_animations(self, queryset, name, value):
        """
        Filter collections with minimum animation count
        """
        if not value:
            return queryset
        
        # This requires annotation in the view
        return queryset.filter(animation_count__gte=value)
    
    def filter_max_animations(self, queryset, name, value):
        """
        Filter collections with maximum animation count
        """
        if not value:
            return queryset
        
        # This requires annotation in the view
        return queryset.filter(animation_count__lte=value)