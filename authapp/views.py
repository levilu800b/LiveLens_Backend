# type: ignore
# authapp/views.py
from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login, logout
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta

from .models import User, EmailVerificationCode, UserPreferences
from .serializers import (
    UserRegistrationSerializer, GoogleSignUpSerializer, EmailVerificationSerializer,
    LoginSerializer, GoogleLoginSerializer, UserProfileSerializer,
    UserPreferencesSerializer, PasswordChangeSerializer, ResendVerificationSerializer
)
from .utils import log_user_activity, send_verification_email

from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
import logging

logger = logging.getLogger(__name__)

try:
    from email_notifications.signals import send_password_change_notification
    from email_notifications.utils import send_welcome_email
    from email_notifications.models import NewsletterSubscription
    EMAIL_NOTIFICATIONS_AVAILABLE = True
except ImportError:
    EMAIL_NOTIFICATIONS_AVAILABLE = False
    logger.warning("Email notifications app not available")


class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            log_user_activity(user, 'signup', 'User registered successfully', request)
            
            return Response({
                'message': 'Registration successful. Please check your email for verification code.',
                'user_id': user.id,
                'email': user.email
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleSignUpView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = GoogleSignUpSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            log_user_activity(user, 'signup', 'User registered with Google', request)
            
            # ADD THIS: Send welcome email for Google signup
            if EMAIL_NOTIFICATIONS_AVAILABLE:
                try:
                    send_welcome_email(user)
                    
                    # Auto-subscribe to newsletter
                    newsletter_subscription, created = NewsletterSubscription.objects.get_or_create(
                        user=user,
                        defaults={
                            'email': user.email,
                            'is_verified': True,
                            'subscription_source': 'account_creation'
                        }
                    )
                    if created:
                        logger.info(f"Auto-subscribed Google user {user.email} to newsletter")
                        
                except Exception as e:
                    logger.error(f"Failed to send welcome email or subscribe to newsletter: {str(e)}")
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            return Response({
                'message': 'Google signup successful.',
                'user': UserProfileSerializer(user, context={'request': request}).data,
                'access_token': str(access_token),
                'refresh_token': str(refresh)
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            log_user_activity(user, 'profile_update', 'Email verified successfully', request)
            
            # ADD THIS: Send welcome email after successful verification
            if EMAIL_NOTIFICATIONS_AVAILABLE:
                try:
                    send_welcome_email(user)
                    
                    # Auto-subscribe to newsletter if email notifications are available
                    newsletter_subscription, created = NewsletterSubscription.objects.get_or_create(
                        user=user,
                        defaults={
                            'email': user.email,
                            'is_verified': True,
                            'subscription_source': 'account_creation'
                        }
                    )
                    if created:
                        logger.info(f"Auto-subscribed user {user.email} to newsletter")
                        
                except Exception as e:
                    logger.error(f"Failed to send welcome email or subscribe to newsletter: {str(e)}")
            
            return Response({
                'message': 'Email verified successfully. You can now log in.',
                'user_id': user.id
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # Update last login
            user.last_login = timezone.now()
            user.save()
            
            log_user_activity(user, 'login', 'User logged in successfully', request)
            
            return Response({
                'message': 'Login successful.',
                'user': UserProfileSerializer(user, context={'request': request}).data,  # ✅ ADD request context!
                'access_token': str(access_token),
                'refresh_token': str(refresh)
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class GoogleLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = GoogleLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # Update last login
            user.last_login = timezone.now()
            user.save()
            
            log_user_activity(user, 'login', 'User logged in with Google', request)
            
            return Response({
                'message': 'Google login successful.',
                'user': UserProfileSerializer(user, context={'request': request}).data,  # ✅ ADD request context!
                'access_token': str(access_token),
                'refresh_token': str(refresh)
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh_token')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            log_user_activity(request.user, 'logout', 'User logged out successfully', request)
            
            return Response({
                'message': 'Logout successful.'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Invalid token or logout failed.'
            }, status=status.HTTP_400_BAD_REQUEST)


class ProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    
    def get(self, request):
        """Get user profile data"""
        # Pass request context for avatar URL building
        serializer = UserProfileSerializer(request.user, context={'request': request})
        profile_data = serializer.data
        
        # ADD THIS: Add newsletter subscription info if available
        if EMAIL_NOTIFICATIONS_AVAILABLE:
            try:
                newsletter_subscription = NewsletterSubscription.objects.filter(
                    user=request.user,
                    is_active=True
                ).first()
                
                if newsletter_subscription:
                    from email_notifications.serializers import NewsletterSubscriptionSerializer
                    profile_data['newsletter_subscription'] = NewsletterSubscriptionSerializer(newsletter_subscription).data
                else:
                    profile_data['newsletter_subscription'] = None
            except Exception as e:
                logger.error(f"Failed to get newsletter subscription info: {str(e)}")
                profile_data['newsletter_subscription'] = None
        
        return Response(profile_data, status=status.HTTP_200_OK)
    
    def put(self, request):
        """Update user profile with field name conversion and proper date handling"""
        try:
            # Convert frontend field names to backend field names
            data = request.data.copy()
            
            # Log incoming data for debugging
            logger.info(f"Profile update request data: {data}")
            
            # Field name mapping from frontend to backend
            field_mapping = {
                'firstName': 'first_name',
                'lastName': 'last_name', 
                'phoneNumber': 'phone_number',
                'dateOfBirth': 'date_of_birth',
                'gender': 'gender',
                'country': 'country',
                'avatar': 'avatar'
            }
            
            # Gender choice mapping
            gender_mapping = {
                'Male': 'M',
                'Female': 'F',
                'male': 'M',
                'female': 'F',
                'M': 'M',
                'F': 'F',
                '': '',
            }
            
            # Convert field names and handle special cases
            converted_data = {}
            for frontend_name, backend_name in field_mapping.items():
                if frontend_name in data:
                    value = data[frontend_name]
                    
                    # Special handling for gender field
                    if frontend_name == 'gender' and value:
                        if value in gender_mapping:
                            converted_value = gender_mapping[value]
                            converted_data[backend_name] = converted_value
                            logger.info(f"Converted gender '{value}' -> '{converted_value}'")
                        else:
                            logger.warning(f"Unknown gender value: {value}")
                            converted_data[backend_name] = value
                    
                    # ✅ FIXED: Special handling for date fields
                    elif frontend_name == 'dateOfBirth':
                        if value and value.strip():  # Only process non-empty dates
                            try:
                                # Validate date format
                                from datetime import datetime
                                datetime.strptime(value, '%Y-%m-%d')
                                converted_data[backend_name] = value
                                logger.info(f"Converted {frontend_name} -> {backend_name}: {value}")
                            except ValueError:
                                logger.warning(f"Invalid date format for {frontend_name}: {value}")
                                # Skip invalid dates rather than causing an error
                                continue
                        else:
                            # ✅ CRITICAL FIX: Set empty dates to None, not empty string
                            converted_data[backend_name] = None
                            logger.info(f"Converted empty {frontend_name} -> {backend_name}: None")
                    
                    # Handle other fields normally
                    else:
                        converted_data[backend_name] = value
                        logger.info(f"Converted {frontend_name} -> {backend_name}: {value}")
            
            # Handle avatar file separately (it might not be in the mapping)
            if 'avatar' in data and data['avatar']:
                converted_data['avatar'] = data['avatar']
                logger.info("Avatar file included in update")
            
            logger.info(f"Converted data: {converted_data}")
            
            # ✅ ADDITIONAL FIX: Clean up empty string fields that should be None
            for field_name, field_value in list(converted_data.items()):
                if isinstance(field_value, str) and field_value.strip() == '':
                    if field_name in ['date_of_birth']:  # Add other date/nullable fields here
                        converted_data[field_name] = None
                        logger.info(f"Cleaned empty string to None for {field_name}")
                    elif field_name in ['phone_number', 'country']:  # Text fields can be empty
                        converted_data[field_name] = ''
            
            # Update user with converted data
            serializer = UserProfileSerializer(
                request.user, 
                data=converted_data, 
                partial=True,  # ✅ Allow partial updates
                context={'request': request}
            )
            
            if serializer.is_valid():
                user = serializer.save()
                
                # Log successful update
                log_user_activity(request.user, 'profile_update', 'Profile updated successfully', request)
                logger.info(f"Profile update successful for user {user.id}")
                
                # Return updated user data with proper context
                updated_serializer = UserProfileSerializer(user, context={'request': request})
                
                return Response({
                    'message': 'Profile updated successfully.',
                    'user': updated_serializer.data
                }, status=status.HTTP_200_OK)
            else:
                # Log validation errors
                logger.error(f"Profile update validation errors: {serializer.errors}")
                
                # Return detailed error information
                error_messages = []
                for field, errors in serializer.errors.items():
                    for error in errors:
                        error_messages.append(f"{field}: {error}")
                
                return Response({
                    'error': 'Validation failed',
                    'details': serializer.errors,
                    'message': '; '.join(error_messages)
                }, status=status.HTTP_400_BAD_REQUEST)
                
        except Exception as e:
            logger.error(f"Profile update error: {str(e)}", exc_info=True)
            return Response({
                'error': 'Profile update failed',
                'message': 'An unexpected error occurred. Please try again.'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
class UserPreferencesView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        preferences, created = UserPreferences.objects.get_or_create(user=request.user)
        serializer = UserPreferencesSerializer(preferences)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request):
        preferences, created = UserPreferences.objects.get_or_create(user=request.user)
        serializer = UserPreferencesSerializer(preferences, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            log_user_activity(request.user, 'profile_update', 'Preferences updated', request)
            
            return Response({
                'message': 'Preferences updated successfully.',
                'preferences': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, user=request.user)
        if serializer.is_valid():
            serializer.save()
            log_user_activity(request.user, 'password_change', 'Password changed successfully', request)
            
            # ADD THIS: Send password change notification email
            if EMAIL_NOTIFICATIONS_AVAILABLE:
                try:
                    send_password_change_notification(request.user, request)
                except Exception as e:
                    logger.error(f"Failed to send password change notification: {str(e)}")
            
            return Response({
                'message': 'Password changed successfully.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ResendVerificationView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            return Response({
                'message': 'Verification code resent successfully. Please check your email.',
                'user_id': user.id
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class DeleteAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request):
        user = request.user
        log_user_activity(user, 'profile_update', 'Account deleted', request)
        
        # Delete user account
        user.delete()
        
        return Response({
            'message': 'Account deleted successfully.'
        }, status=status.HTTP_200_OK)


class CheckEmailView(APIView):
    """Check if email exists in the system"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({
                'error': 'Email is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        exists = User.objects.filter(email=email).exists()
        return Response({
            'exists': exists
        }, status=status.HTTP_200_OK)


class UserStatsView(APIView):
    """Get user statistics for the profile"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        user = request.user
        
        # Import here to avoid circular imports
        from stories.models import Story
        from media_content.models import Film, Content
        from podcasts.models import Podcast
        from animations.models import Animation
        from comments.models import Comment
        
        # Count user interactions
        stats = {
            'total_stories_read': 0,  # Will be calculated from user activity
            'total_videos_watched': 0,  # Will be calculated from user activity
            'total_comments': Comment.objects.filter(user=user).count(),
            'total_likes': 0,  # Will be calculated from user activity
            'member_since': user.created_at.strftime('%B %Y'),
            'last_activity': user.last_login.strftime('%B %d, %Y at %I:%M %p') if user.last_login else 'Never'
        }
        
        return Response(stats, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_dashboard(request):
    """Get user dashboard data"""
    user = request.user
    
    # This will be expanded when we add the content models
    dashboard_data = {
        'user': UserProfileSerializer(user).data,
        'recent_activities': [],  # Will be populated from user activities
        'recommendations': [],  # Will be populated from AI recommendations
        'continue_watching': [],  # Will be populated from user viewing history
        'favorites': [],  # Will be populated from user favorites
    }
    
    return Response(dashboard_data, status=status.HTTP_200_OK)