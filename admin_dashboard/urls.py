# admin_dashboard/urls.py
# type: ignore

from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    # Dashboard overview
    path('overview/', views.dashboard_overview, name='dashboard_overview'),
    path('analytics/', views.analytics_summary, name='analytics_summary'),
    path('user-stats/', views.user_management_stats, name='user_management_stats'),
    
    # Content analytics
    path('content-analytics/', views.ContentAnalyticsListView.as_view(), name='content_analytics_list'),
    
    # User activities
    path('user-activities/', views.UserActivityListView.as_view(), name='user_activities_list'),
    
    # System alerts
    path('alerts/', views.SystemAlertListCreateView.as_view(), name='alert_list_create'),
    path('alerts/<uuid:pk>/', views.SystemAlertDetailView.as_view(), name='alert_detail'),
    path('alerts/mark-read/', views.mark_alerts_as_read, name='mark_alerts_read'),
    path('alerts/<uuid:alert_id>/resolve/', views.resolve_alert, name='resolve_alert'),
    
    # Reports
    path('reports/', views.ReportGenerationListCreateView.as_view(), name='report_list_create'),
    path('reports/<uuid:report_id>/download/', views.download_report, name='download_report'),
]
