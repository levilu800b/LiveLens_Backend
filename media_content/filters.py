# type: ignore

# media_content/filters.py
import django_filters
from django.db.models import Q
from .models import Film, Content

class FilmFilter(django_filters.FilterSet):
    """
    Filter for Film model with comprehensive filtering options
    """
    # Text search
    search = django_filters.CharFilter(method='filter_search', help_text="Search in title, description, director, cast")
    
    # Category filter
    category = django_filters.ChoiceFilter(choices=Film.CATEGORY_CHOICES)
    
    # Status filter
    status = django_filters.ChoiceFilter(choices=Film.STATUS_CHOICES)
    
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
    
    # Rating filter
    mpaa_rating = django_filters.ChoiceFilter(choices=[
        ('G', 'G - General Audiences'),
        ('PG', 'PG - Parental Guidance'),
        ('PG-13', 'PG-13 - Parents Strongly Cautioned'),
        ('R', 'R - Restricted'),
        ('NC-17', 'NC-17 - Adults Only'),
        ('NR', 'Not Rated'),
    ])
    
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
    video_quality = django_filters.ChoiceFilter(choices=Film.QUALITY_CHOICES)
    
    # Language filter
    language = django_filters.CharFilter(lookup_expr='icontains')
    
    # Director filter
    director = django_filters.CharFilter(lookup_expr='icontains')
    
    # Tags filter
    tags = django_filters.CharFilter(method='filter_tags', help_text="Filter by tags (comma-separated)")
    
    # Series filter
    series_name = django_filters.CharFilter(lookup_expr='icontains')
    
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
            'title': 'Title',
        }
    )
    
    class Meta:
        model = Film
        fields = [
            'category', 'status', 'author_id', 'is_featured', 'is_trending',
            'is_premium', 'is_series', 'release_year', 'mpaa_rating', 'video_quality',
            'language'
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
            Q(cast__icontains=value) |
            Q(tags__icontains=value) |
            Q(studio__icontains=value)
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
        
        # Filter films that contain any of the specified tags
        query = Q()
        for tag in tags:
            query |= Q(tags__icontains=tag)
        
        return queryset.filter(query)

class ContentFilter(django_filters.FilterSet):
    """
    Filter for Content model with comprehensive filtering options
    """
    # Text search
    search = django_filters.CharFilter(method='filter_search', help_text="Search in title, description, creator, series")
    
    # Category filter
    category = django_filters.ChoiceFilter(choices=Content.CATEGORY_CHOICES)
    
    # Content type filter
    content_type = django_filters.ChoiceFilter(choices=Content.CONTENT_TYPE_CHOICES)
    
    # Status filter
    status = django_filters.ChoiceFilter(choices=Content.STATUS_CHOICES)
    
    # Author filter
    author = django_filters.CharFilter(method='filter_author', help_text="Filter by author username or name")
    author_id = django_filters.UUIDFilter(field_name='author__id')
    
    # Boolean filters
    is_featured = django_filters.BooleanFilter()
    is_trending = django_filters.BooleanFilter()
    is_premium = django_filters.BooleanFilter()
    is_live = django_filters.BooleanFilter()
    
    # Date filters
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    published_after = django_filters.DateTimeFilter(field_name='published_at', lookup_expr='gte')
    published_before = django_filters.DateTimeFilter(field_name='published_at', lookup_expr='lte')
    
    # Year filter
    release_year = django_filters.NumberFilter()
    release_year_after = django_filters.NumberFilter(field_name='release_year', lookup_expr='gte')
    release_year_before = django_filters.NumberFilter(field_name='release_year', lookup_expr='lte')
    
    # Difficulty level filter
    difficulty_level = django_filters.ChoiceFilter(choices=[
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ])
    
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
    video_quality = django_filters.ChoiceFilter(choices=Content.QUALITY_CHOICES)
    
    # Language filter
    language = django_filters.CharFilter(lookup_expr='icontains')
    
    # Creator filter
    creator = django_filters.CharFilter(lookup_expr='icontains')
    
    # Tags filter
    tags = django_filters.CharFilter(method='filter_tags', help_text="Filter by tags (comma-separated)")
    
    # Series filter
    series_name = django_filters.CharFilter(lookup_expr='icontains')
    
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
            'title': 'Title',
        }
    )
    
    class Meta:
        model = Content
        fields = [
            'category', 'content_type', 'status', 'author_id', 'is_featured',
            'is_trending', 'is_premium', 'is_live', 'release_year', 'difficulty_level',
            'video_quality', 'language'
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
            Q(creator__icontains=value) |
            Q(series_name__icontains=value) |
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
        
        # Filter content that contains any of the specified tags
        query = Q()
        for tag in tags:
            query |= Q(tags__icontains=tag)
        
        return queryset.filter(query)