# sneak_peeks/urls.py
# type: ignore

from django.urls import path
from . import views

app_name = 'sneak_peeks'

urlpatterns = [
    # Main sneak peek endpoints
    path('', views.SneakPeekListCreateView.as_view(), name='sneak_peek_list_create'),
    path('<slug:slug>/', views.SneakPeekDetailView.as_view(), name='sneak_peek_detail'),
    
    # Sneak peek interactions
    path('<slug:sneak_peek_slug>/interact/', views.sneak_peek_interaction, name='sneak_peek_interaction'),
    path('<slug:sneak_peek_slug>/track-progress/', views.track_watch_progress, name='track_watch_progress'),
    
    # Playlist endpoints
    path('playlists/', views.SneakPeekPlaylistListCreateView.as_view(), name='playlist_list_create'),
    path('playlists/<uuid:pk>/', views.SneakPeekPlaylistDetailView.as_view(), name='playlist_detail'),
    
    # User-specific endpoints
    path('history/', views.user_sneak_peek_history, name='user_history'),
    path('favorites/', views.user_favorites, name='user_favorites'),
    
    # Statistics
    path('stats/', views.sneak_peek_stats, name='sneak_peek_stats'),
]