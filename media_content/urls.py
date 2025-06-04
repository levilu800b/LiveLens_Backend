# type: ignore

# media_content/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'media_content'

# DRF Router for ViewSets
router = DefaultRouter()
router.register(r'films', views.FilmViewSet, basename='film')
router.register(r'content', views.ContentViewSet, basename='content')
router.register(r'collections', views.MediaCollectionViewSet, basename='collection')
router.register(r'playlists', views.PlaylistViewSet, basename='playlist')

urlpatterns = [
    # ViewSet URLs
    path('', include(router.urls)),
    
    # Custom API views
    path('hero/', views.HeroMediaView.as_view(), name='hero_media'),
    path('search/', views.MediaSearchView.as_view(), name='media_search'),
    path('stats/', views.MediaStatsView.as_view(), name='media_stats'),
    path('library/', views.MediaLibraryView.as_view(), name='media_library'),
    path('track-view/<str:media_type>/<uuid:media_id>/', views.TrackMediaViewAPIView.as_view(), name='track_media_view'),
]
