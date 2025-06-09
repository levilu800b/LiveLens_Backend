# sneak_peeks/filters.py
# type: ignore

import django_filters
from django.db.models import Q
from .models import SneakPeek

class SneakPeekFilter(django_filters.FilterSet):
    """Filter for sneak peeks"""
    
    category = django_filters.CharFilter(field_name='category', lookup_expr='iexact')
    tags = django_filters.CharFilter(method='filter_tags')
    author = django_filters.CharFilter(field_name='author__username', lookup_expr='icontains')
    release_year = django_filters.NumberFilter(field_name='release_date', lookup_expr='year')
    content_rating = django_filters.CharFilter(field_name='content_rating', lookup_expr='iexact')
    duration_min = django_filters.NumberFilter(field_name='duration', lookup_expr='gte')
    duration_max = django_filters.NumberFilter(field_name='duration', lookup_expr='lte')
    is_featured = django_filters.BooleanFilter(field_name='is_featured')
    is_trending = django_filters.BooleanFilter(field_name='is_trending')
    is_premium = django_filters.BooleanFilter(field_name='is_premium')
    
    class Meta:
        model = SneakPeek
        fields = [
            'category', 'tags', 'author', 'release_year', 'content_rating',
            'duration_min', 'duration_max', 'is_featured', 'is_trending', 'is_premium'
        ]
    
    def filter_tags(self, queryset, name, value):
        """Filter by tags (comma-separated)"""
        if not value:
            return queryset
        
        tags = [tag.strip() for tag in value.split(',')]
        query = Q()
        for tag in tags:
            query |= Q(tags__icontains=tag)
        
        return queryset.filter(query)