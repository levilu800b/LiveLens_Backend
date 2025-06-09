# analytics/urls.py - CORRECTED VERSION
# type: ignore

from django.urls import path
from . import views

app_name = 'analytics'

urlpatterns = [
    # Content tracking
    path('track-view/', views.track_content_view_endpoint, name='track_view'),
    path('update-progress/', views.update_view_progress_endpoint, name='update_progress'),
    path('track-engagement/', views.track_engagement_endpoint, name='track_engagement'),
    
    # Analytics data
    path('content/<str:content_type>/<uuid:content_id>/', views.ContentAnalyticsView.as_view(), name='content_analytics'),
    path('user/<uuid:user_id>/', views.UserAnalyticsView.as_view(), name='user_analytics'),
    path('dashboard/', views.AnalyticsDashboardView.as_view(), name='analytics_dashboard'),
    
    # Reports
    path('reports/generate/', views.GenerateAnalyticsReportView.as_view(), name='generate_report'),
]
