# ai_service/views.py
# type: ignore

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from django.utils import timezone
from django.core.cache import cache
from datetime import datetime, timedelta
import logging

# Import AI utilities
from utils.ai_integration import (
    generate_ai_story, generate_ai_animation, generate_ai_subtitles,
    generate_daily_ai_post, create_tts_config, ai_service
)

# Import models
from stories.models import Story
from animations.models import Animation
from authapp.permissions import IsAdminUser, CanManageContent

logger = logging.getLogger(__name__)

class AIStoryGenerationView(APIView):
    """
    Generate AI stories for admin content creation
    POST /api/ai/generate-story/
    """
    permission_classes = [CanManageContent]
    
    def post(self, request):
        try:
            prompt = request.data.get('prompt')
            if not prompt:
                return Response({
                    'error': 'Prompt is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get additional parameters
            genre = request.data.get('genre', 'general')
            length = request.data.get('length', 'medium')
            tone = request.data.get('tone', 'engaging')
            
            # Generate story using AI
            generated_story = generate_ai_story(
                prompt=prompt,
                genre=genre,
                length=length,
                tone=tone,
                max_tokens=request.data.get('max_tokens', 2000)
            )
            
            if not generated_story:
                return Response({
                    'error': 'Failed to generate story. Please try again.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Optionally save as draft
            save_as_draft = request.data.get('save_as_draft', False)
            story_id = None
            
            if save_as_draft:
                # Generate title from first line or prompt
                title = generated_story.split('\n')[0][:100] or f"AI Generated Story - {prompt[:50]}"
                
                story = Story.objects.create(
                    title=title,
                    content=generated_story,
                    author=request.user,
                    status='draft',
                    category=genre,
                    is_ai_generated=True,
                    ai_prompt=prompt
                )
                story_id = str(story.id)
            
            return Response({
                'success': True,
                'generated_story': generated_story,
                'metadata': {
                    'prompt': prompt,
                    'genre': genre,
                    'length': length,
                    'tone': tone,
                    'word_count': len(generated_story.split()),
                    'character_count': len(generated_story)
                },
                'story_id': story_id,
                'message': 'Story generated successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating AI story: {e}")
            return Response({
                'error': 'Story generation failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AIAnimationGenerationView(APIView):
    """
    Generate AI animation scripts for admin content creation
    POST /api/ai/generate-animation/
    """
    permission_classes = [CanManageContent]
    
    def post(self, request):
        try:
            description = request.data.get('description')
            if not description:
                return Response({
                    'error': 'Animation description is required'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Get additional parameters
            style = request.data.get('style', '2D animation')
            duration = request.data.get('duration', '2-3 minutes')
            target_audience = request.data.get('target_audience', 'general')
            
            # Generate animation script using AI
            generated_animation = generate_ai_animation(
                description=description,
                style=style,
                duration=duration,
                target_audience=target_audience,
                max_tokens=request.data.get('max_tokens', 1500)
            )
            
            if not generated_animation:
                return Response({
                    'error': 'Failed to generate animation script. Please try again.'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Optionally save as draft
            save_as_draft = request.data.get('save_as_draft', False)
            animation_id = None
            
            if save_as_draft:
                title = f"AI Animation - {description[:50]}"
                
                animation = Animation.objects.create(
                    title=title,
                    description=description,
                    author=request.user,
                    status='generating',
                    animation_software='AI Generated',
                    is_ai_generated=True,
                    ai_prompt=description,
                    ai_script=generated_animation.get('full_script', '')
                )
                animation_id = str(animation.id)
            
            return Response({
                'success': True,
                'generated_animation': generated_animation,
                'metadata': {
                    'description': description,
                    'style': style,
                    'duration': duration,
                    'target_audience': target_audience,
                    'scenes_count': len(generated_animation.get('scenes', []))
                },
                'animation_id': animation_id,
                'message': 'Animation script generated successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating AI animation: {e}")
            return Response({
                'error': 'Animation generation failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class AISubtitleGenerationView(APIView):
    """
    Generate subtitles for video content
    POST /api/ai/generate-subtitles/
    """
    permission_classes = [CanManageContent]
    
    def post(self, request):
        try:
            text = request.data.get('text')
            video_id = request.data.get('video_id')
            
            if not text:
                return Response({
                    'error': 'Text content is required for subtitle generation'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Generate subtitles
            subtitles = generate_ai_subtitles(
                text=text,
                words_per_minute=request.data.get('words_per_minute', 150)
            )
            
            if not subtitles:
                return Response({
                    'error': 'Failed to generate subtitles'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Convert to standard subtitle format
            subtitle_formats = {
                'srt': self._convert_to_srt(subtitles),
                'vtt': self._convert_to_vtt(subtitles),
                'json': subtitles
            }
            
            return Response({
                'success': True,
                'subtitles': subtitle_formats,
                'metadata': {
                    'total_duration': subtitles[-1]['end_time'] if subtitles else 0,
                    'subtitle_count': len(subtitles),
                    'estimated_wpm': request.data.get('words_per_minute', 150)
                },
                'message': 'Subtitles generated successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating subtitles: {e}")
            return Response({
                'error': 'Subtitle generation failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    def _convert_to_srt(self, subtitles):
        """Convert subtitle data to SRT format"""
        srt_content = ""
        for i, subtitle in enumerate(subtitles, 1):
            start_time = self._seconds_to_srt_time(subtitle['start_time'])
            end_time = self._seconds_to_srt_time(subtitle['end_time'])
            
            srt_content += f"{i}\n"
            srt_content += f"{start_time} --> {end_time}\n"
            srt_content += f"{subtitle['text']}\n\n"
        
        return srt_content
    
    def _convert_to_vtt(self, subtitles):
        """Convert subtitle data to WebVTT format"""
        vtt_content = "WEBVTT\n\n"
        for subtitle in subtitles:
            start_time = self._seconds_to_vtt_time(subtitle['start_time'])
            end_time = self._seconds_to_vtt_time(subtitle['end_time'])
            
            vtt_content += f"{start_time} --> {end_time}\n"
            vtt_content += f"{subtitle['text']}\n\n"
        
        return vtt_content
    
    def _seconds_to_srt_time(self, seconds):
        """Convert seconds to SRT time format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        millisecs = int((seconds % 1) * 1000)
        return f"{hours:02d}:{minutes:02d}:{secs:02d},{millisecs:03d}"
    
    def _seconds_to_vtt_time(self, seconds):
        """Convert seconds to WebVTT time format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours:02d}:{minutes:02d}:{secs:06.3f}"

class AIVoiceOverGenerationView(APIView):
    """
    Generate voice-over configuration for text content
    POST /api/ai/generate-voiceover/
    """
    permission_classes = [CanManageContent]
    
    def post(self, request):
        try:
            text = request.data.get('text')
            if not text:
                return Response({
                    'error': 'Text content is required for voice-over generation'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            voice_style = request.data.get('voice_style', 'natural')
            
            # Generate TTS configuration
            tts_config = create_tts_config(text, voice_style)
            
            if not tts_config:
                return Response({
                    'error': 'Failed to generate voice-over configuration'
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            return Response({
                'success': True,
                'tts_config': tts_config,
                'message': 'Voice-over configuration generated successfully'
            }, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Error generating voice-over config: {e}")
            return Response({
                'error': 'Voice-over generation failed',
                'details': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def daily_live_post(request):
    """
    Get daily AI-generated live post for landing page
    GET /api/ai/daily-post/
    """
    
    try:
        # Determine time of day
        current_hour = timezone.now().hour
        if 5 <= current_hour < 12:
            time_of_day = 'morning'
        elif 12 <= current_hour < 18:
            time_of_day = 'afternoon'
        else:
            time_of_day = 'evening'
        
        # Check cache first
        cache_key = f"daily_post_{time_of_day}_{timezone.now().date()}"
        cached_post = cache.get(cache_key)
        
        if cached_post:
            return Response({
                'success': True,
                'post': cached_post,
                'time_of_day': time_of_day,
                'cached': True
            }, status=status.HTTP_200_OK)
        
        # Get trending content for suggestions
        trending_content = []
        try:
            from stories.models import Story
            from media_content.models import Film
            
            trending_stories = Story.objects.filter(
                status='published'
            ).order_by('-view_count')[:3]
            
            trending_films = Film.objects.filter(
                status='published'
            ).order_by('-view_count')[:2]
            
            trending_content = [story.title for story in trending_stories]
            trending_content.extend([film.title for film in trending_films])
            
        except Exception as e:
            logger.warning(f"Could not fetch trending content: {e}")
        
        # Generate daily post
        daily_post = generate_daily_ai_post(time_of_day, trending_content)
        
        # Cache for 4 hours
        cache.set(cache_key, daily_post, 14400)
        
        return Response({
            'success': True,
            'post': daily_post,
            'time_of_day': time_of_day,
            'suggested_content': trending_content[:3],
            'generated_at': timezone.now().isoformat()
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error generating daily post: {e}")
        return Response({
            'success': False,
            'error': 'Failed to generate daily post',
            'fallback_post': "Welcome to our streaming platform! Discover amazing stories, films, and animations."
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
@permission_classes([CanManageContent])
def ai_service_status(request):
    """
    Check AI service status and configuration
    GET /api/ai/status/
    """
    
    try:
        status_info = {
            'ai_configured': ai_service.is_configured(),
            'google_ai_available': bool(ai_service.api_key),
            'model_name': 'gemini-pro',
            'features': {
                'story_generation': True,
                'animation_script_generation': True,
                'subtitle_generation': True,
                'voice_over_config': True,
                'daily_posts': True
            },
            'service_health': 'healthy' if ai_service.is_configured() else 'unavailable'
        }
        
        # Test AI service with a simple call
        if ai_service.is_configured():
            try:
                test_result = generate_ai_story("Test prompt", max_tokens=50)
                status_info['last_test'] = 'success' if test_result else 'failed'
            except Exception as e:
                status_info['last_test'] = f'failed: {str(e)}'
                status_info['service_health'] = 'degraded'
        
        return Response(status_info, status=status.HTTP_200_OK)
        
    except Exception as e:
        logger.error(f"Error checking AI service status: {e}")
        return Response({
            'error': 'Failed to check AI service status',
            'service_health': 'unknown'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)