# type: ignore

# stories/filters.py
import django_filters
from .models import Story, StoryCategory


class StoryFilter(django_filters.FilterSet):
    title = django_filters.CharFilter(lookup_expr='icontains')
    categories = django_filters.ModelMultipleChoiceFilter(
        queryset=StoryCategory.objects.all(),
        to_field_name='slug',
        conjoined=False  # OR condition
    )
    tags = django_filters.CharFilter(method='filter_by_tags')
    min_reading_time = django_filters.NumberFilter(field_name='estimated_reading_time', lookup_expr='gte')
    max_reading_time = django_filters.NumberFilter(field_name='estimated_reading_time', lookup_expr='lte')
    is_featured = django_filters.BooleanFilter()
    is_trending = django_filters.BooleanFilter()
    author = django_filters.CharFilter(field_name='author__username', lookup_expr='icontains')
    date_from = django_filters.DateFilter(field_name='published_at', lookup_expr='gte')
    date_to = django_filters.DateFilter(field_name='published_at', lookup_expr='lte')
    
    class Meta:
        model = Story
        fields = [
            'title', 'categories', 'tags', 'min_reading_time', 
            'max_reading_time', 'is_featured', 'is_trending', 
            'author', 'date_from', 'date_to'
        ]
    
    def filter_by_tags(self, queryset, name, value):
        """Filter stories by tags (case-insensitive partial match)"""
        if value:
            return queryset.filter(tags__icontains=value)
        return queryset