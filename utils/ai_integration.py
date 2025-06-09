# utils/ai_integration.py
# type: ignore

import google.generativeai as genai
from django.conf import settings
from typing import Optional, Dict, Any
import logging
import json
import asyncio
from asgiref.sync import sync_to_async

logger = logging.getLogger(__name__)

class GoogleAIService:
    """
    Service class for Google AI integration
    """
    
    def __init__(self):
        self.api_key = settings.AI_SETTINGS.get('GOOGLE_AI_API_KEY')
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel(settings.AI_SETTINGS.get('DEFAULT_AI_MODEL', 'gemini-pro'))
        else:
            logger.warning("Google AI API key not configured")
            self.model = None
    
    def is_configured(self) -> bool:
        """Check if AI service is properly configured"""
        return self.model is not None
    
    def generate_story(self, prompt: str, **kwargs) -> Optional[str]:
        """
        Generate a story using AI
        
        Args:
            prompt: The story prompt/description
            **kwargs: Additional parameters like length, genre, etc.
        
        Returns:
            Generated story content or None if failed
        """
        if not self.is_configured():
            logger.error("Google AI not configured")
            return None
        
        try:
            # Enhance the prompt with additional parameters
            enhanced_prompt = self._build_story_prompt(prompt, **kwargs)
            
            response = self.model.generate_content(
                enhanced_prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=kwargs.get('max_tokens', 2000),
                    temperature=kwargs.get('temperature', 0.7),
                )
            )
            
            return response.text if response.text else None
            
        except Exception as e:
            logger.error(f"Error generating story: {e}")
            return None
    
    def generate_animation_script(self, description: str, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Generate animation script and description
        
        Args:
            description: Animation description
            **kwargs: Additional parameters
        
        Returns:
            Dictionary with script, scenes, and metadata
        """
        if not self.is_configured():
            logger.error("Google AI not configured")
            return None
        
        try:
            prompt = self._build_animation_prompt(description, **kwargs)
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=kwargs.get('max_tokens', 1500),
                    temperature=kwargs.get('temperature', 0.8),
                )
            )
            
            if response.text:
                # Parse the response into structured format
                return self._parse_animation_response(response.text)
            
            return None
            
        except Exception as e:
            logger.error(f"Error generating animation script: {e}")
            return None
    
    def generate_subtitles(self, text: str, **kwargs) -> Optional[list]:
        """
        Generate subtitles with timestamps (mock implementation)
        
        Args:
            text: Text content to create subtitles for
            **kwargs: Additional parameters
        
        Returns:
            List of subtitle entries with timestamps
        """
        if not text:
            return None
        
        try:
            # Split text into sentences
            sentences = text.split('. ')
            subtitles = []
            
            # Estimate timing (rough calculation)
            words_per_minute = kwargs.get('words_per_minute', 150)
            current_time = 0
            
            for i, sentence in enumerate(sentences):
                if sentence.strip():
                    # Clean up sentence
                    clean_sentence = sentence.strip()
                    if not clean_sentence.endswith('.'):
                        clean_sentence += '.'
                    
                    # Calculate duration based on word count
                    word_count = len(clean_sentence.split())
                    duration = (word_count / words_per_minute) * 60  # Convert to seconds
                    
                    subtitle_entry = {
                        'id': i + 1,
                        'start_time': current_time,
                        'end_time': current_time + duration,
                        'text': clean_sentence
                    }
                    
                    subtitles.append(subtitle_entry)
                    current_time += duration + 0.5  # Add small pause between sentences
            
            return subtitles
            
        except Exception as e:
            logger.error(f"Error generating subtitles: {e}")
            return None
    
    def text_to_speech_description(self, text: str, voice_style: str = "natural") -> Optional[Dict[str, Any]]:
        """
        Generate text-to-speech parameters and description
        
        Args:
            text: Text to convert to speech
            voice_style: Style of voice (natural, dramatic, calm, etc.)
        
        Returns:
            Dictionary with TTS parameters and metadata
        """
        try:
            # This would integrate with actual TTS service
            # For now, return structured description
            
            tts_config = {
                'text': text,
                'voice_style': voice_style,
                'language': 'en-US',
                'speed': 1.0,
                'pitch': 0,
                'volume': 0.8,
                'estimated_duration': len(text.split()) / 2.5,  # Rough estimation
                'ssml_enhanced': self._enhance_text_with_ssml(text, voice_style)
            }
            
            return tts_config
            
        except Exception as e:
            logger.error(f"Error creating TTS description: {e}")
            return None
    
    def generate_daily_live_post(self, time_of_day: str, content_suggestions: list = None) -> Optional[str]:
        """
        Generate daily live post content for the landing page
        
        Args:
            time_of_day: 'morning', 'afternoon', or 'evening'
            content_suggestions: List of content to potentially recommend
        
        Returns:
            Generated live post text
        """
        if not self.is_configured():
            return self._fallback_daily_post(time_of_day)
        
        try:
            prompt = self._build_daily_post_prompt(time_of_day, content_suggestions)
            
            response = self.model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    max_output_tokens=200,
                    temperature=0.8,
                )
            )
            
            return response.text if response.text else self._fallback_daily_post(time_of_day)
            
        except Exception as e:
            logger.error(f"Error generating daily post: {e}")
            return self._fallback_daily_post(time_of_day)
    
    def _build_story_prompt(self, prompt: str, **kwargs) -> str:
        """Build enhanced prompt for story generation"""
        
        genre = kwargs.get('genre', 'general')
        length = kwargs.get('length', 'medium')
        tone = kwargs.get('tone', 'engaging')
        
        enhanced_prompt = f"""
        Create a {tone} {length}-length story in the {genre} genre based on this prompt:
        
        {prompt}
        
        Please structure the story with:
        - A compelling opening
        - Well-developed characters
        - A clear narrative arc
        - Engaging dialogue where appropriate
        - A satisfying conclusion
        
        Make it suitable for a digital storytelling platform.
        """
        
        return enhanced_prompt
    
    def _build_animation_prompt(self, description: str, **kwargs) -> str:
        """Build prompt for animation script generation"""
        
        style = kwargs.get('style', '2D animation')
        duration = kwargs.get('duration', '2-3 minutes')
        target_audience = kwargs.get('target_audience', 'general')
        
        prompt = f"""
        Create an animation script for a {duration} {style} animation suitable for {target_audience} audience.
        
        Description: {description}
        
        Please provide:
        1. A detailed scene-by-scene breakdown
        2. Character descriptions and movements
        3. Visual style notes
        4. Audio/sound effect suggestions
        5. Timing estimates for each scene
        
        Format the response as a structured script that can be used for animation production.
        """
        
        return prompt
    
    def _build_daily_post_prompt(self, time_of_day: str, content_suggestions: list) -> str:
        """Build prompt for daily live post generation"""
        
        content_info = ""
        if content_suggestions:
            content_info = f"Today's featured content includes: {', '.join(content_suggestions[:3])}"
        
        time_greetings = {
            'morning': 'Good morning',
            'afternoon': 'Good afternoon', 
            'evening': 'Good evening'
        }
        
        greeting = time_greetings.get(time_of_day, 'Hello')
        
        prompt = f"""
        Create a warm, engaging {time_of_day} greeting for visitors to a content streaming platform.
        
        Requirements:
        - Start with "{greeting}"
        - Keep it under 150 words
        - Be encouraging and positive
        - {content_info if content_info else "Include a motivational message or interesting fact"}
        - Make it feel personal and welcoming
        - Sometimes include inspirational quotes or affirmations
        
        The tone should be friendly, uplifting, and make visitors excited to explore content.
        """
        
        return prompt
    
    def _parse_animation_response(self, response_text: str) -> Dict[str, Any]:
        """Parse AI response into structured animation data"""
        
        try:
            # Basic parsing - in a real implementation, this would be more sophisticated
            lines = response_text.split('\n')
            
            parsed_data = {
                'full_script': response_text,
                'scenes': [],
                'characters': [],
                'estimated_duration': '2-3 minutes',
                'style_notes': '',
                'audio_notes': ''
            }
            
            current_scene = None
            for line in lines:
                line = line.strip()
                if line.startswith('Scene') or line.startswith('SCENE'):
                    if current_scene:
                        parsed_data['scenes'].append(current_scene)
                    current_scene = {'title': line, 'description': '', 'duration': ''}
                elif current_scene and line:
                    current_scene['description'] += line + ' '
            
            if current_scene:
                parsed_data['scenes'].append(current_scene)
            
            return parsed_data
            
        except Exception as e:
            logger.error(f"Error parsing animation response: {e}")
            return {'full_script': response_text, 'scenes': [], 'characters': []}
    
    def _enhance_text_with_ssml(self, text: str, voice_style: str) -> str:
        """Enhance text with SSML tags for better speech synthesis"""
        
        # Basic SSML enhancement based on voice style
        ssml_map = {
            'dramatic': '<prosody rate="medium" pitch="+2st">',
            'calm': '<prosody rate="slow" pitch="-1st">',
            'energetic': '<prosody rate="fast" pitch="+1st">',
            'natural': '<prosody rate="medium" pitch="0st">'
        }
        
        opening_tag = ssml_map.get(voice_style, '<prosody rate="medium">')
        closing_tag = '</prosody>'
        
        return f"<speak>{opening_tag}{text}{closing_tag}</speak>"
    
    def _fallback_daily_post(self, time_of_day: str) -> str:
        """Fallback daily posts when AI is not available"""
        
        fallback_posts = {
            'morning': [
                "Good morning! Start your day with inspiration. Explore our latest stories and content to fuel your creativity and motivation.",
                "Good morning, creators! Today is full of possibilities. Dive into our collection of stories, films, and animations to spark your imagination.",
                "Good morning! Every great day starts with great content. Discover something new in our ever-growing library of creative works."
            ],
            'afternoon': [
                "Good afternoon! Taking a break? Perfect time to explore our featured content and discover your next favorite story or film.",
                "Good afternoon, everyone! Need some midday inspiration? Check out our trending animations and podcast episodes.",
                "Good afternoon! Recharge your creativity with our handpicked selection of stories and visual content."
            ],
            'evening': [
                "Good evening! Unwind with our premium collection of films, stories, and animations. Perfect for a relaxing evening.",
                "Good evening, storytellers! End your day with powerful narratives and creative content that inspire and entertain.",
                "Good evening! As the day winds down, explore our peaceful collection of content designed to inspire and relax."
            ]
        }
        
        import random
        posts = fallback_posts.get(time_of_day, fallback_posts['morning'])
        return random.choice(posts)

# Global AI service instance
ai_service = GoogleAIService()

# Convenience functions
def generate_ai_story(prompt: str, **kwargs) -> Optional[str]:
    """Convenience function for story generation"""
    return ai_service.generate_story(prompt, **kwargs)

def generate_ai_animation(description: str, **kwargs) -> Optional[Dict[str, Any]]:
    """Convenience function for animation generation"""
    return ai_service.generate_animation_script(description, **kwargs)

def generate_ai_subtitles(text: str, **kwargs) -> Optional[list]:
    """Convenience function for subtitle generation"""
    return ai_service.generate_subtitles(text, **kwargs)

def generate_daily_ai_post(time_of_day: str, content_suggestions: list = None) -> str:
    """Convenience function for daily post generation"""
    return ai_service.generate_daily_live_post(time_of_day, content_suggestions) or "Welcome to our platform!"

def create_tts_config(text: str, voice_style: str = "natural") -> Optional[Dict[str, Any]]:
    """Convenience function for TTS configuration"""
    return ai_service.text_to_speech_description(text, voice_style)