# type: ignore

# stories/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Story categories
    path('categories/', views.StoryCategoryListView.as_view(), name='story-categories'),
    path('categories/<slug:slug>/', views.StoryCategoryDetailView.as_view(), name='story-category-detail'),
    
    # Stories
    path('', views.StoryListView.as_view(), name='story-list'),
    path('featured/', views.featured_stories, name='featured-stories'),
    path('trending/', views.trending_stories, name='trending-stories'),
    path('latest/', views.latest_stories, name='latest-stories'),
    path('my-stories/', views.UserStoriesView.as_view(), name='user-stories'),
    path('reading-progress/', views.user_story_progress, name='user-story-progress'),
    
    # Story detail and interactions
    path('<slug:slug>/', views.StoryDetailView.as_view(), name='story-detail'),
    path('<slug:story_slug>/like/', views.toggle_story_like, name='toggle-story-like'),
    path('<slug:story_slug>/progress/', views.update_reading_progress, name='update-reading-progress'),
    
    # Story pages
    path('<slug:story_slug>/pages/', views.StoryPageListView.as_view(), name='story-pages'),
    path('<slug:story_slug>/pages/<int:pk>/', views.StoryPageDetailView.as_view(), name='story-page-detail'),
    
    # Story illustrations
    path('<slug:story_slug>/illustrations/', views.StoryIllustrationListView.as_view(), name='story-illustrations'),
    path('<slug:story_slug>/illustrations/<int:pk>/', views.StoryIllustrationDetailView.as_view(), name='story-illustration-detail'),
]