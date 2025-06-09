# recommendations/urls.py
# type: ignore

from django.urls import path
from . import views

app_name = 'recommendations'

urlpatterns = [
    # User recommendations
    path('', views.UserRecommendationsView.as_view(), name='user_recommendations'),
    path('update-engagement/', views.update_recommendation_engagement, name='update_engagement'),
    
    # Admin recommendation management
    path('generate-bulk/', views.AdminGenerateBulkRecommendationsView.as_view(), name='admin_generate_bulk'),
    path('stats/', views.RecommendationStatsView.as_view(), name='recommendation_stats'),
]
