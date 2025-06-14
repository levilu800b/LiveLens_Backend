# type: ignore

# animations/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'animations'

# DRF Router for ViewSets
router = DefaultRouter()
router.register(r'animations', views.AnimationViewSet, basename='animation')
router.register(r'collections', views.AnimationCollectionViewSet, basename='collection')
router.register(r'playlists', views.AnimationPlaylistViewSet, basename='playlist')

urlpatterns = [
    # ViewSet URLs
    path('', include(router.urls)),
    
    # Custom API views
    path('hero/', views.HeroAnimationView.as_view(), name='hero_animation'),
    path('search/', views.AnimationSearchView.as_view(), name='animation_search'),
    path('stats/', views.AnimationStatsView.as_view(), name='animation_stats'),
    path('library/', views.AnimationLibraryView.as_view(), name='animation_library'),
    path('track-view/<uuid:animation_id>/', views.TrackAnimationViewAPIView.as_view(), name='track_animation_view'),
]