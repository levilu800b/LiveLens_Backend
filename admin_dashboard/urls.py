# ===================================================================
# admin_dashboard/urls.py
# type: ignore

from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    # Dashboard overview
    path('stats/', views.dashboard_stats, name='dashboard_stats'),
    
    # Content management
    path('content/', views.content_management, name='content_management'),
    path('content/<str:content_type>/<int:content_id>/delete/', views.delete_content, name='delete_content'),
    
    # User management
    path('users/', views.user_management, name='user_management'),
    path('users/<int:user_id>/make-admin/', views.make_user_admin, name='make_user_admin'),
    path('users/<int:user_id>/remove-admin/', views.remove_user_admin, name='remove_user_admin'),
    path('users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
    
    # Admin activities
    path('activities/', views.admin_activities, name='admin_activities'),
    
    # Moderation queue
    path('moderation/', views.moderation_queue, name='moderation_queue'),
]