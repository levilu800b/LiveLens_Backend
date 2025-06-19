# authapp/secure_views.py - SECURE AUTHENTICATION WITH HTTP-ONLY COOKIES
# type: ignore


from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.conf import settings
from django.http import JsonResponse
import json
from datetime import datetime, timedelta
from .serializers import UserProfileSerializer


class SecureCookieAuthentication:
    """Utility class for secure cookie management"""
    
    @staticmethod
    def set_auth_cookies(response, access_token, refresh_token):
        """Set HTTP-only cookies for tokens"""
        # Access token (short-lived, HTTP-only)
        response.set_cookie(
            'access_token',
            access_token,
            max_age=settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME').total_seconds(),
            httponly=True,  # CRITICAL: Prevents JavaScript access
            secure=not settings.DEBUG,  # HTTPS in production
            samesite='Lax',  # CSRF protection
            domain=settings.SESSION_COOKIE_DOMAIN
        )
        
        # Refresh token (long-lived, HTTP-only)
        response.set_cookie(
            'refresh_token', 
            refresh_token,
            max_age=settings.SIMPLE_JWT.get('REFRESH_TOKEN_LIFETIME').total_seconds(),
            httponly=True,  # CRITICAL: Prevents JavaScript access
            secure=not settings.DEBUG,  # HTTPS in production
            samesite='Lax',  # CSRF protection
            domain=settings.SESSION_COOKIE_DOMAIN
        )
    
    @staticmethod
    def clear_auth_cookies(response):
        """Clear authentication cookies"""
        response.delete_cookie('access_token')
        response.delete_cookie('refresh_token')


class SecureLoginView(APIView):
    """Secure login that sets HTTP-only cookies"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        password = request.data.get('password')
        
        if not email or not password:
            return Response({
                'error': 'Email and password are required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Authenticate user
        user = authenticate(email=email, password=password)
        if not user:
            return Response({
                'error': 'Invalid email or password.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return Response({
                'error': 'Account is deactivated.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_verified:
            return Response({
                'error': 'Please verify your email address first.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Create response with user data (NO TOKENS IN JSON)
        response_data = {
            'message': 'Login successful',
            'user': UserProfileSerializer(user).data
        }
        
        response = Response(response_data, status=status.HTTP_200_OK)
        
        # Set secure HTTP-only cookies
        SecureCookieAuthentication.set_auth_cookies(
            response, access_token, refresh_token
        )
        
        return response


class SecureGoogleLoginView(APIView):
    """Secure Google login that sets HTTP-only cookies"""
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        email = request.data.get('email')
        google_id = request.data.get('google_id')
        
        if not email or not google_id:
            return Response({
                'error': 'Email and Google ID are required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Find user by email or Google ID
            user = User.objects.get(email=email)
            
            # Update Google ID if not set
            if not user.google_id:
                user.google_id = google_id
                user.save()
        
        except User.DoesNotExist:
            return Response({
                'error': 'User not found. Please sign up first.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if not user.is_active:
            return Response({
                'error': 'Account is deactivated.'
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        
        # Create response with user data (NO TOKENS IN JSON)
        response_data = {
            'message': 'Google login successful',
            'user': UserProfileSerializer(user).data
        }
        
        response = Response(response_data, status=status.HTTP_200_OK)
        
        # Set secure HTTP-only cookies
        SecureCookieAuthentication.set_auth_cookies(
            response, access_token, refresh_token
        )
        
        return response


class SecureLogoutView(APIView):
    """Secure logout that clears HTTP-only cookies"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            # Get refresh token from cookie
            refresh_token = request.COOKIES.get('refresh_token')
            
            if refresh_token:
                # Blacklist the refresh token
                token = RefreshToken(refresh_token)
                token.blacklist()
        
        except Exception as e:
            # Continue with logout even if token blacklisting fails
            pass
        
        response = Response({
            'message': 'Logout successful'
        }, status=status.HTTP_200_OK)
        
        # Clear cookies
        SecureCookieAuthentication.clear_auth_cookies(response)
        
        return response


class SecureProfileView(APIView):
    """Secure profile view that uses cookie authentication"""
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Get user profile"""
        serializer = UserProfileSerializer(request.user)
        return Response({
            'user': serializer.data
        }, status=status.HTTP_200_OK)
    
    def put(self, request):
        """Update user profile"""
        serializer = UserProfileSerializer(
            request.user, 
            data=request.data, 
            partial=True
        )
        
        if serializer.is_valid():
            updated_user = serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                'user': UserProfileSerializer(updated_user).data
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ===== CUSTOM AUTHENTICATION MIDDLEWARE =====
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth.models import AnonymousUser


class CookieJWTAuthentication(JWTAuthentication):
    """Custom JWT Authentication that reads from HTTP-only cookies"""
    
    def authenticate(self, request):
        # Try to get token from cookie first
        raw_token = request.COOKIES.get('access_token')
        
        if raw_token is None:
            # Fallback to header authentication for API clients
            header = self.get_header(request)
            if header is None:
                return None
            raw_token = self.get_raw_token(header)
        
        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
        except TokenError:
            # Try to refresh token if access token is invalid
            refresh_token = request.COOKIES.get('refresh_token')
            if refresh_token:
                try:
                    refresh = RefreshToken(refresh_token)
                    new_access_token = str(refresh.access_token)
                    
                    # Validate the new token
                    validated_token = self.get_validated_token(new_access_token)
                    
                    # Set the new token in the response
                    # Note: This requires middleware to handle response modification
                    request._new_access_token = new_access_token
                    
                except TokenError:
                    return None
            else:
                return None

        return self.get_user(validated_token), validated_token


# ===== MIDDLEWARE FOR TOKEN REFRESH =====
class TokenRefreshMiddleware:
    """Middleware to set new access token cookies after refresh"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        
        # If a new access token was generated during authentication
        if hasattr(request, '_new_access_token'):
            response.set_cookie(
                'access_token',
                request._new_access_token,
                max_age=settings.SIMPLE_JWT.get('ACCESS_TOKEN_LIFETIME').total_seconds(),
                httponly=True,
                secure=not settings.DEBUG,
                samesite='Lax',
                domain=settings.SESSION_COOKIE_DOMAIN
            )
        
        return response