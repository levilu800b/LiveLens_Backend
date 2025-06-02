# type: ignore
# authapp/views.py


from rest_framework import status, generics, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import login
from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction

from .models import User, EmailVerification, UserActivity, UserLibrary, UserFavorites
from .serializers import (
    UserRegistrationSerializer, EmailVerificationSerializer, UserLoginSerializer,
    UserProfileSerializer, UserUpdateSerializer, UserActivitySerializer,
    UserLibrarySerializer, UserFavoritesSerializer, PasswordChangeSerializer
)
from .utils import send_verification_email


class UserRegistrationView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        with transaction.atomic():
            user = serializer.save()
            
            # Create and send verification code
            verification = EmailVerification.objects.create(user=user)
            send_verification_email(user.email, verification.code)
            
        return Response({
            'message': 'User registered successfully. Please check your email for verification code.',
            'user_id': user.id
        }, status=status.HTTP_201_CREATED)


class EmailVerificationView(generics.GenericAPIView):
    serializer_class = EmailVerificationSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        verification = serializer.validated_data['verification']
        
        with transaction.atomic():
            user.is_verified = True
            user.save()
            
            verification.is_used = True
            verification.save()
        
        return Response({
            'message': 'Email verified successfully. You can now log in.'
        }, status=status.HTTP_200_OK)


class ResendVerificationView(generics.GenericAPIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        
        if not email:
            return Response({
                'error': 'Email is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'error': 'User with this email does not exist.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        if user.is_verified:
            return Response({
                'message': 'User is already verified.'
            }, status=status.HTTP_200_OK)
        
        # Create new verification code
        verification = EmailVerification.objects.create(user=user)
        send_verification_email(user.email, verification.code)
        
        return Response({
            'message': 'Verification code sent successfully.'
        }, status=status.HTTP_200_OK)


class UserLoginView(generics.GenericAPIView):
    serializer_class = UserLoginSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        access_token = refresh.access_token
        
        # Add custom claims
        access_token['is_admin'] = user.is_admin
        access_token['full_name'] = user.full_name
        
        return Response({
            'access_token': str(access_token),
            'refresh_token': str(refresh),
            'user': UserProfileSerializer(user).data
        }, status=status.HTTP_200_OK)


class UserProfileView(generics.RetrieveUpdateAPIView):
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            return UserUpdateSerializer
        return UserProfileSerializer


class ChangePasswordView(generics.GenericAPIView):
    serializer_class = PasswordChangeSerializer
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        
        return Response({
            'message': 'Password changed successfully.'
        }, status=status.HTTP_200_OK)


class DeleteAccountView(generics.DestroyAPIView):
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def destroy(self, request, *args, **kwargs):
        user = self.get_object()
        user.delete()
        
        return Response({
            'message': 'Account deleted successfully.'
        }, status=status.HTTP_204_NO_CONTENT)


class UserLibraryView(generics.ListCreateAPIView):
    serializer_class = UserLibrarySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserLibrary.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserLibraryDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = UserLibrarySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserLibrary.objects.filter(user=self.request.user)


class UserFavoritesView(generics.ListCreateAPIView):
    serializer_class = UserFavoritesSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserFavorites.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class UserFavoritesDetailView(generics.RetrieveDestroyAPIView):
    serializer_class = UserFavoritesSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserFavorites.objects.filter(user=self.request.user)


class UserActivityView(generics.ListCreateAPIView):
    serializer_class = UserActivitySerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return UserActivity.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth(request):
    """Handle Google OAuth authentication"""
    # This will be implemented with Google OAuth library
    # For now, return a placeholder response
    return Response({
        'message': 'Google authentication endpoint - to be implemented'
    }, status=status.HTTP_501_NOT_IMPLEMENTED)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Handle user logout"""
    try:
        refresh_token = request.data.get('refresh_token')
        if refresh_token:
            token = RefreshToken(refresh_token)
            token.blacklist()
        
        return Response({
            'message': 'Logged out successfully.'
        }, status=status.HTTP_200_OK)
    except Exception as e:
        return Response({
            'error': 'Invalid token.'
        }, status=status.HTTP_400_BAD_REQUEST)