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
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            return Response({
                'message': 'Google signup successful.',
                'user': UserProfileSerializer(user).data,
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
                'user': UserProfileSerializer(user).data,
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
                'user': UserProfileSerializer(user).data,
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
    
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request):
        serializer = UserProfileSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            log_user_activity(request.user, 'profile_update', 'Profile updated successfully', request)
            
            return Response({
                'message': 'Profile updated successfully.',
                'user': serializer.data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


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