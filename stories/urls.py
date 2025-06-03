# type: ignore

# stories/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'stories'

# DRF Router for ViewSets
router = DefaultRouter()
router.register(r'stories', views.StoryViewSet, basename='story')
router.register(r'collections', views.StoryCollectionViewSet, basename='collection')

urlpatterns = [
    # ViewSet URLs
    path('', include(router.urls)),
    
    # Custom API views
    path('hero/', views.HeroStoryView.as_view(), name='hero_story'),
    path('search/', views.StorySearchView.as_view(), name='story_search'),
    path('stats/', views.StoryStatsView.as_view(), name='story_stats'),
    path('track-view/<uuid:story_id>/', views.TrackStoryViewAPIView.as_view(), name='track_story_view'),
]
