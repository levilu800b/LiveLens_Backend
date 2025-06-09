# user_library/urls.py
# type: ignore

from django.urls import path
from . import views

app_name = 'user_library'

urlpatterns = [
    # Library management
    path('', views.UserLibraryListView.as_view(), name='library_list'),
    path('update-progress/', views.UpdateProgressView.as_view(), name='update_progress'),
    path('dashboard-summary/', views.user_dashboard_summary, name='dashboard_summary'),
    
    # Favorites
    path('favorites/', views.UserFavoritesListView.as_view(), name='favorites_list'),
    path('toggle-favorite/', views.ToggleFavoriteView.as_view(), name='toggle_favorite'),
    
    # Playlists
    path('playlists/', views.UserPlaylistListCreateView.as_view(), name='playlist_list_create'),
    path('playlists/<uuid:pk>/', views.UserPlaylistDetailView.as_view(), name='playlist_detail'),
    path('playlists/<uuid:playlist_id>/add-item/', views.AddToPlaylistView.as_view(), name='add_to_playlist'),
    
    # Recommendations
    path('recommendations/', views.user_recommendations, name='recommendations'),
]