# comments/urls.py
# type: ignore

from django.urls import path
from . import views

app_name = 'comments'

urlpatterns = [
    # Main comment endpoints
    path('', views.CommentListCreateView.as_view(), name='comment_list_create'),
    path('<uuid:pk>/', views.CommentDetailView.as_view(), name='comment_detail'),
    
    # Comment interactions
    path('<uuid:comment_id>/interact/', views.comment_interaction, name='comment_interaction'),
    
    # User-specific endpoints
    path('my-comments/', views.user_comments, name='user_comments'),
    path('notifications/', views.comment_notifications, name='comment_notifications'),
    
    # Moderation endpoints (admin only)
    path('moderation/', views.comment_moderation, name='comment_moderation'),
    path('<uuid:comment_id>/moderate/', views.moderate_comment, name='moderate_comment'),
    
    # Statistics
    path('stats/', views.comment_stats, name='comment_stats'),
]