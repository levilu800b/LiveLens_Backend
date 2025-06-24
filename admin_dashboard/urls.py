# ===================================================================
# admin_dashboard/urls.py
# type: ignore

from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    # Your existing URLs...
    path('stats/', views.dashboard_stats, name='dashboard_stats'),
    path('content/', views.content_management, name='content_management'),
    path('users/', views.user_management, name='user_management'),
    path('users/<uuid:user_id>/make-admin/', views.make_user_admin, name='make_user_admin'),
    path('users/<uuid:user_id>/remove-admin/', views.remove_user_admin, name='remove_user_admin'),
    path('users/<uuid:user_id>/delete/', views.delete_user, name='delete_user'),
    path('content/<str:content_type>/<uuid:content_id>/delete/', views.delete_content, name='delete_content'),
    path('activities/', views.admin_activities, name='admin_activities'),
    path('moderation/', views.moderation_queue, name='moderation_queue'),
    
    # ADD THESE NEW LINES:
    path('live/start/', views.start_live_stream, name='start_live_stream'),
    path('notifications/stats/', views.email_notification_stats, name='email_notification_stats'),
    path('notifications/send-content/', views.send_content_notification, name='send_content_notification'),
]