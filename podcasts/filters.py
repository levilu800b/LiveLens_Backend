# type: ignore

# podcasts/filters.py
import django_filters
from django.db.models import Q
from .models import PodcastSeries, Podcast

class PodcastSeriesFilter(django_filters.FilterSet):
    """
    Filter for PodcastSeries model with comprehensive filtering options
    """
    # Text search
    search = django_filters.CharFilter(method='filter_search', help_text="Search in title, description, host")
    
    # Category filter
    category = django_filters.ChoiceFilter(choices=PodcastSeries.CATEGORY_CHOICES)
    
    # Language filter
    language = django_filters.ChoiceFilter(choices=PodcastSeries.LANGUAGE_CHOICES)
    
    # Author filter
    author = django_filters.CharFilter(method='filter_author', help_text="Filter by author username or name")
    author_id = django_filters.UUIDFilter(field_name='author__id')
    
    # Boolean filters
    is_active = django_filters.BooleanFilter()
    is_featured = django_filters.BooleanFilter()
    is_explicit = django_filters.BooleanFilter()
    
    # Date filters
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Host filter
    host = django_filters.CharFilter(lookup_expr='icontains')
    
    # Tags filter
    tags = django_filters.CharFilter(method='filter_tags', help_text="Filter by tags (comma-separated)")
    
    # Episode count filters
    min_episodes = django_filters.NumberFilter(method='filter_min_episodes')
    max_episodes = django_filters.NumberFilter(method='filter_max_episodes')
    
    # Ordering
    ordering = django_filters.OrderingFilter(
        fields=(
            ('created_at', 'created'),
            ('updated_at', 'updated'),
            ('title', 'title'),
            ('episode_count', 'episode_count'),
        ),
        field_labels={
            'created': 'Date Created',
            'updated': 'Date Updated',
            'title': 'Title',
            'episode_count': 'Episode Count',
        }
    )
    
    class Meta:
        model = PodcastSeries
        fields = [
            'category', 'language', 'author_id', 'is_active', 'is_featured', 'is_explicit'
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
            Q(host__icontains=value) |
            Q(tags__icontains=value)
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
        
        # Filter series that contain any of the specified tags
        query = Q()
        for tag in tags:
            query |= Q(tags__icontains=tag)
        
        return queryset.filter(query)
    
    def filter_min_episodes(self, queryset, name, value):
        """
        Filter series with minimum episode count
        """
        if not value:
            return queryset
        
        # This requires annotation in the view
        return queryset.filter(episode_count__gte=value)
    
    def filter_max_episodes(self, queryset, name, value):
        """
        Filter series with maximum episode count
        """
        if not value:
            return queryset
        
        # This requires annotation in the view
        return queryset.filter(episode_count__lte=value)

class PodcastFilter(django_filters.FilterSet):
    """
    Filter for Podcast model with comprehensive filtering options
    """
    # Text search
    search = django_filters.CharFilter(method='filter_search', help_text="Search in title, description, guest, series")
    
    # Series filter
    series = django_filters.UUIDFilter(field_name='series__id')
    series_title = django_filters.CharFilter(field_name='series__title', lookup_expr='icontains')
    
    # Episode filters
    episode_number = django_filters.NumberFilter()
    season_number = django_filters.NumberFilter()
    episode_type = django_filters.ChoiceFilter(choices=Podcast.EPISODE_TYPE_CHOICES)
    
    # Status filter
    status = django_filters.ChoiceFilter(choices=Podcast.STATUS_CHOICES)
    
    # Author filter
    author = django_filters.CharFilter(method='filter_author', help_text="Filter by author username or name")
    author_id = django_filters.UUIDFilter(field_name='author__id')
    
    # Boolean filters
    is_featured = django_filters.BooleanFilter()
    is_premium = django_filters.BooleanFilter()
    is_explicit = django_filters.BooleanFilter()
    
    # Date filters
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    published_after = django_filters.DateTimeFilter(field_name='published_at', lookup_expr='gte')
    published_before = django_filters.DateTimeFilter(field_name='published_at', lookup_expr='lte')
    
    # Numeric filters
    min_play_count = django_filters.NumberFilter(field_name='play_count', lookup_expr='gte')
    max_play_count = django_filters.NumberFilter(field_name='play_count', lookup_expr='lte')
    min_like_count = django_filters.NumberFilter(field_name='like_count', lookup_expr='gte')
    max_like_count = django_filters.NumberFilter(field_name='like_count', lookup_expr='lte')
    min_duration = django_filters.NumberFilter(field_name='duration', lookup_expr='gte')
    max_duration = django_filters.NumberFilter(field_name='duration', lookup_expr='lte')
    min_rating = django_filters.NumberFilter(field_name='average_rating', lookup_expr='gte')
    max_rating = django_filters.NumberFilter(field_name='average_rating', lookup_expr='lte')
    
    # Audio quality filter
    audio_quality = django_filters.ChoiceFilter(choices=[
        ('64kbps', '64 kbps'),
        ('128kbps', '128 kbps'),
        ('192kbps', '192 kbps'),
        ('256kbps', '256 kbps'),
        ('320kbps', '320 kbps'),
    ])
    
    # Guest filter
    guest = django_filters.CharFilter(lookup_expr='icontains')
    
    # Tags filter
    tags = django_filters.CharFilter(method='filter_tags', help_text="Filter by tags (comma-separated)")
    
    # Category filter (from series)
    category = django_filters.ChoiceFilter(field_name='series__category', choices=PodcastSeries.CATEGORY_CHOICES)
    
    # Language filter (from series)
    language = django_filters.ChoiceFilter(field_name='series__language', choices=PodcastSeries.LANGUAGE_CHOICES)
    
    # Ordering
    ordering = django_filters.OrderingFilter(
        fields=(
            ('created_at', 'created'),
            ('updated_at', 'updated'),
            ('published_at', 'published'),
            ('play_count', 'play_count'),
            ('like_count', 'like_count'),
            ('average_rating', 'rating'),
            ('duration', 'duration'),
            ('episode_number', 'episode_number'),
            ('title', 'title'),
        ),
        field_labels={
            'created': 'Date Created',
            'updated': 'Date Updated',
            'published': 'Date Published',
            'play_count': 'Play Count',
            'like_count': 'Like Count',
            'rating': 'Average Rating',
            'duration': 'Duration',
            'episode_number': 'Episode Number',
            'title': 'Title',
        }
    )
    
    class Meta:
        model = Podcast
        fields = [
            'series', 'episode_number', 'season_number', 'episode_type', 'status',
            'author_id', 'is_featured', 'is_premium', 'is_explicit', 'audio_quality',
            'category', 'language'
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
            Q(summary__icontains=value) |
            Q(guest__icontains=value) |
            Q(tags__icontains=value) |
            Q(series__title__icontains=value) |
            Q(series__host__icontains=value)
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
        
        # Filter episodes that contain any of the specified tags
        query = Q()
        for tag in tags:
            query |= Q(tags__icontains=tag) | Q(series__tags__icontains=tag)
        
        return queryset.filter(query)