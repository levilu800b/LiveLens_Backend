# ai_service/urls.py
# type: ignore

from django.urls import path
from . import views

app_name = 'ai_service'

urlpatterns = [
    # AI Content Generation
    path('generate-story/', views.AIStoryGenerationView.as_view(), name='generate_story'),
    path('generate-animation/', views.AIAnimationGenerationView.as_view(), name='generate_animation'),
    path('generate-subtitles/', views.AISubtitleGenerationView.as_view(), name='generate_subtitles'),
    path('generate-voiceover/', views.AIVoiceOverGenerationView.as_view(), name='generate_voiceover'),
    
    # Daily Content
    path('daily-post/', views.daily_live_post, name='daily_live_post'),
    
    # Service Management
    path('status/', views.ai_service_status, name='ai_service_status'),
]