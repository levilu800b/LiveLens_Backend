# type: ignore

# podcasts/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'podcasts'

# DRF Router for ViewSets
router = DefaultRouter()
router.register(r'series', views.PodcastSeriesViewSet, basename='series')
router.register(r'episodes', views.PodcastViewSet, basename='episode')
router.register(r'playlists', views.PodcastPlaylistViewSet, basename='playlist')

urlpatterns = [
    # ViewSet URLs
    path('', include(router.urls)),
    
    # Custom API views
    path('hero/', views.HeroPodcastView.as_view(), name='hero_podcast'),
    path('search/', views.PodcastSearchView.as_view(), name='podcast_search'),
    path('stats/', views.PodcastStatsView.as_view(), name='podcast_stats'),
    path('library/', views.PodcastLibraryView.as_view(), name='podcast_library'),
    path('track-listen/<uuid:podcast_id>/', views.TrackPodcastListenAPIView.as_view(), name='track_podcast_listen'),
]