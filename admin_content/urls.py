# admin_content/urls.py
# type: ignore

from django.urls import path
from . import views

app_name = 'admin_content'

urlpatterns = [
    # Content management
    path('all/', views.AdminContentListView.as_view(), name='admin_content_list'),
    path('statistics/', views.admin_content_statistics, name='admin_content_statistics'),
    path('filters/', views.admin_content_filters, name='admin_content_filters'),
    
    # Content creation
    path('stories/create/', views.AdminStoryCreateView.as_view(), name='admin_story_create'),
    path('animations/create/', views.AdminAnimationCreateView.as_view(), name='admin_animation_create'),
    
    # Content update and delete
    path('<str:content_type>/<uuid:content_id>/update/', views.AdminContentUpdateView.as_view(), name='admin_content_update'),
    path('<str:content_type>/<uuid:content_id>/delete/', views.AdminContentDeleteView.as_view(), name='admin_content_delete'),
    
    # Bulk actions
    path('bulk-actions/', views.AdminContentBulkActionsView.as_view(), name='admin_content_bulk_actions'),
]