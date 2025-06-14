# live_video/urls.py
# type: ignore

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

app_name = 'live_video'

# Create a router for ViewSets
router = DefaultRouter()
router.register(r'live-videos', views.LiveVideoViewSet, basename='live-video')
router.register(r'schedules', views.LiveVideoScheduleViewSet, basename='live-video-schedule')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Live Video Comments/Chat endpoints
    path(
        'live-videos/<slug:slug>/comments/', 
        views.live_video_comments, 
        name='live-video-comments'
    ),
    
    # Statistics endpoint
    path('stats/', views.live_video_stats, name='live-video-stats'),
    
    # Real-time status endpoint
    path('status/', views.current_live_status, name='current-live-status'),
    
    # Admin-specific endpoints
    path('admin/create-upload/', views.create_live_video_upload, name='admin-create-live-video'),
    path('admin/dashboard/', views.admin_live_video_dashboard, name='admin-dashboard'),
]

# The router automatically creates these URLs:
# GET /api/live-video/live-videos/ - List all live videos
# POST /api/live-video/live-videos/ - Create new live video
# GET /api/live-video/live-videos/{slug}/ - Get specific live video
# PUT /api/live-video/live-videos/{slug}/ - Update live video
# PATCH /api/live-video/live-videos/{slug}/ - Partial update live video
# DELETE /api/live-video/live-videos/{slug}/ - Delete live video

# Custom actions created by the ViewSet:
# GET /api/live-video/live-videos/live_now/ - Get currently live videos
# GET /api/live-video/live-videos/upcoming/ - Get upcoming live videos
# GET /api/live-video/live-videos/featured/ - Get featured live videos
# GET /api/live-video/live-videos/hero_live/ - Get hero live video for landing page
# POST /api/live-video/live-videos/{slug}/interact/ - Interact with live video (like, bookmark, join, leave)
# GET /api/live-video/live-videos/{slug}/watch_stream/ - Get stream info for watching
# POST /api/live-video/live-videos/{slug}/start_stream/ - Start live stream (admin)
# POST /api/live-video/live-videos/{slug}/end_stream/ - End live stream (admin)
# GET /api/live-video/live-videos/my_live_videos/ - Get user's live videos
# GET /api/live-video/live-videos/my_watched/ - Get user's watched live videos
# GET /api/live-video/live-videos/my_bookmarks/ - Get user's bookmarked live videos

# Schedule endpoints:
# GET /api/live-video/schedules/ - List user's schedules
# POST /api/live-video/schedules/ - Create new schedule
# GET /api/live-video/schedules/{id}/ - Get specific schedule
# PUT /api/live-video/schedules/{id}/ - Update schedule
# DELETE /api/live-video/schedules/{id}/ - Delete schedule
# POST /api/live-video/schedules/{id}/create_live_video/ - Create live video from schedule