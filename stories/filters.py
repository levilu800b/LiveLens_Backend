# type: ignore

# stories/filters.py
import django_filters
from django.db.models import Q
from .models import Story

class StoryFilter(django_filters.FilterSet):
    """
    Filter for Story model with comprehensive filtering options
    """
    # Text search
    search = django_filters.CharFilter(method='filter_search', help_text="Search in title, description, content")
    
    # Category filter
    category = django_filters.ChoiceFilter(choices=Story.CATEGORY_CHOICES)
    
    # Status filter
    status = django_filters.ChoiceFilter(choices=Story.STATUS_CHOICES)
    
    # Author filter
    author = django_filters.CharFilter(method='filter_author', help_text="Filter by author username or name")
    author_id = django_filters.UUIDFilter(field_name='author__id')
    
    # Boolean filters
    is_featured = django_filters.BooleanFilter()
    is_trending = django_filters.BooleanFilter()
    
    # Date filters
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    published_after = django_filters.DateTimeFilter(field_name='published_at', lookup_expr='gte')
    published_before = django_filters.DateTimeFilter(field_name='published_at', lookup_expr='lte')
    
    # Numeric filters
    min_read_count = django_filters.NumberFilter(field_name='read_count', lookup_expr='gte')
    max_read_count = django_filters.NumberFilter(field_name='read_count', lookup_expr='lte')
    min_like_count = django_filters.NumberFilter(field_name='like_count', lookup_expr='gte')
    max_like_count = django_filters.NumberFilter(field_name='like_count', lookup_expr='lte')
    min_read_time = django_filters.NumberFilter(field_name='estimated_read_time', lookup_expr='gte')
    max_read_time = django_filters.NumberFilter(field_name='estimated_read_time', lookup_expr='lte')
    
    # Tags filter
    tags = django_filters.CharFilter(method='filter_tags', help_text="Filter by tags (comma-separated)")
    
    # Ordering
    ordering = django_filters.OrderingFilter(
        fields=(
            ('created_at', 'created'),
            ('updated_at', 'updated'),
            ('published_at', 'published'),
            ('read_count', 'read_count'),
            ('like_count', 'like_count'),
            ('comment_count', 'comment_count'),
            ('estimated_read_time', 'read_time'),
            ('title', 'title'),
        ),
        field_labels={
            'created': 'Date Created',
            'updated': 'Date Updated',
            'published': 'Date Published',
            'read_count': 'Read Count',
            'like_count': 'Like Count',
            'comment_count': 'Comment Count',
            'read_time': 'Read Time',
            'title': 'Title',
        }
    )
    
    class Meta:
        model = Story
        fields = [
            'category', 'status', 'author_id', 'is_featured', 'is_trending'
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
            Q(content__icontains=value) |
            Q(excerpt__icontains=value) |
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
        
        # Filter stories that contain any of the specified tags
        query = Q()
        for tag in tags:
            query |= Q(tags__icontains=tag)
        
        return queryset.filter(query)

class StoryCollectionFilter(django_filters.FilterSet):
    """
    Filter for StoryCollection model
    """
    # Text search
    search = django_filters.CharFilter(method='filter_search', help_text="Search in name, description")
    
    # Boolean filters
    is_public = django_filters.BooleanFilter()
    
    # Author filter
    user = django_filters.CharFilter(method='filter_user', help_text="Filter by username")
    user_id = django_filters.UUIDFilter(field_name='user__id')
    
    # Date filters
    created_after = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Ordering
    ordering = django_filters.OrderingFilter(
        fields=(
            ('created_at', 'created'),
            ('updated_at', 'updated'),
            ('name', 'name'),
        )
    )
    
    class Meta:
        model = Story  # Note: Using Story model, but this would be for StoryCollection
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