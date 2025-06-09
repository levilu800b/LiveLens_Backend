# search/urls.py
# type: ignore

from django.urls import path
from . import views

app_name = 'search'

urlpatterns = [
    path('', views.UniversalSearchView.as_view(), name='universal_search'),
    path('suggestions/', views.SearchSuggestionsView.as_view(), name='search_suggestions'),
    path('filters/', views.search_filters, name='search_filters'),
]