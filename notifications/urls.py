# notifications/urls.py - CORRECTED VERSION
# type: ignore

from django.urls import path
from . import views  # This is the correct import

app_name = 'notifications'

urlpatterns = [
    # Notification management
    path('', views.NotificationListView.as_view(), name='notification_list'),
    path('<uuid:notification_id>/read/', views.mark_notification_read, name='mark_read'),
    path('<uuid:notification_id>/click/', views.mark_notification_clicked, name='mark_clicked'),
    path('mark-all-read/', views.mark_all_notifications_read, name='mark_all_read'),
    path('unread-count/', views.get_unread_count, name='unread_count'),
    
    # Notification settings
    path('settings/', views.NotificationSettingsView.as_view(), name='notification_settings'),
    
    # Admin notification management
    path('send-bulk/', views.AdminBulkNotificationView.as_view(), name='admin_send_bulk'),
    path('templates/', views.NotificationTemplateListView.as_view(), name='notification_templates'),
]