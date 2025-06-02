# type: ignore
# authapp/views.py


from rest_framework import status, permissions, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, logout
from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import EmailVerification, UserLibrary, UserFavorites
from .serializers import (
    UserRegistrationSerializer, UserLoginSerializer, EmailVerificationSerializer,
    ResendVerificationSerializer, UserProfileSerializer, UserProfileUpdateSerializer,
    ChangePasswordSerializer, UserLibrarySerializer, UserLibraryCreateSerializer,
    UserFavoritesSerializer, UserFavoritesCreateSerializer, UserListSerializer
)
import random
import string

User = get_user_model()

class UserRegistrationView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Send verification email
            verification = EmailVerification.objects.filter(user=user).first()
            self.send_verification_email(user, verification.code)
            
            return Response({
                'message': 'User registered successfully. Please check your email for verification code.',
                'user_id': user.id,
                'email': user.email
            }, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def send_verification_email(self, user, code):
        subject = 'Verify Your Email - Streaming Platform'
        context = {
            'user': user,
            'code': code,
            'site_name': 'Streaming Platform'
        }
        
        # HTML email content
        html_message = f"""
        <html>
        <body>
            <h2>Welcome to Streaming Platform!</h2>
            <p>Hi {user.first_name},</p>
            <p>Thank you for registering with us. Please use the following code to verify your email:</p>
            <h3 style="color: #007bff; font-size: 24px; letter-spacing: 2px;">{code}</h3>
            <p>This code will expire in 15 minutes.</p>
            <p>If you didn't create this account, please ignore this email.</p>
            <br>
            <p>Best regards,<br>Streaming Platform Team</p>
        </body>
        </html>
        """
        
        plain_message = f"""
        Welcome to Streaming Platform!
        
        Hi {user.first_name},
        
        Thank you for registering with us. Please use the following code to verify your email:
        
        {code}
        
        This code will expire in 15 minutes.
        
        If you didn't create this account, please ignore this email.
        
        Best regards,
        Streaming Platform Team
        """
        
        send_mail(
            subject,
            plain_message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            html_message=html_message,
            fail_silently=False,
        )

class EmailVerificationView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            verification = serializer.validated_data['verification']
            
            # Mark user as verified
            user.is_verified = True
            user.save()
            
            # Mark verification as used
            verification.is_used = True
            verification.save()
            
            return Response({
                'message': 'Email verified successfully. You can now log in.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ResendVerificationView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            user = User.objects.get(email=email)
            
            # Generate new verification code
            code = ''.join(random.choices(string.digits, k=6))
            EmailVerification.objects.create(user=user, code=code)
            
            # Send email
            UserRegistrationView().send_verification_email(user, code)
            
            return Response({
                'message': 'Verification code sent successfully.'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLoginView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.validated_data['user']
            
            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            # Update last login
            user.save(update_fields=['last_login'])
            
            return Response({
                'message': 'Login successful',
                'user': UserProfileSerializer(user).data,
                'tokens': {
                    'access': str(access_token),
                    'refresh': str(refresh),
                }
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserLogoutView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            logout(request)
            return Response({
                'message': 'Logout successful'
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                'error': 'Invalid token'
            }, status=status.HTTP_400_BAD_REQUEST)

class UserProfileView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        serializer = UserProfileSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    def put(self, request):
        serializer = UserProfileUpdateSerializer(request.user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Profile updated successfully',
                'user': UserProfileSerializer(request.user).data
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = ChangePasswordSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            
            return Response({
                'message': 'Password changed successfully'
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DeleteAccountView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request):
        user = request.user
        user.delete()
        
        return Response({
            'message': 'Account deleted successfully'
        }, status=status.HTTP_200_OK)

# User Library Views
class UserLibraryListView(generics.ListAPIView):
    serializer_class = UserLibrarySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserLibrary.objects.filter(user=self.request.user)

class UserLibraryCreateView(generics.CreateAPIView):
    serializer_class = UserLibraryCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserLibraryUpdateView(generics.UpdateAPIView):
    serializer_class = UserLibraryCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserLibrary.objects.filter(user=self.request.user)

# User Favorites Views
class UserFavoritesListView(generics.ListAPIView):
    serializer_class = UserFavoritesSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserFavorites.objects.filter(user=self.request.user)

class UserFavoritesCreateView(generics.CreateAPIView):
    serializer_class = UserFavoritesCreateSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class UserFavoritesDeleteView(generics.DestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return UserFavorites.objects.filter(user=self.request.user)
    
    def get_object(self):
        content_type = self.request.data.get('content_type')
        content_id = self.request.data.get('content_id')
        
        return UserFavorites.objects.get(
            user=self.request.user,
            content_type=content_type,
            content_id=content_id
        )

# Admin Views
class UserListView(generics.ListAPIView):
    """Admin only - List all users"""
    serializer_class = UserListSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = User.objects.all()
    
    def get(self, request, *args, **kwargs):
        if not request.user.is_admin:
            return Response({
                'error': 'Permission denied. Admin access required.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        return super().get(request, *args, **kwargs)

class MakeUserAdminView(APIView):
    """Admin only - Make a user admin"""
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        if not request.user.is_admin:
            return Response({
                'error': 'Permission denied. Admin access required.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        user_id = request.data.get('user_id')
        try:
            user = User.objects.get(id=user_id)
            user.is_admin_user = True
            user.save()
            
            return Response({
                'message': f'User {user.email} is now an admin.'
            }, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({
                'error': 'User not found.'
            }, status=status.HTTP_404_NOT_FOUND)

class DeleteUserView(APIView):
    """Admin only - Delete a user"""
    permission_classes = [permissions.IsAuthenticated]
    
    def delete(self, request, user_id):
        if not request.user.is_admin:
            return Response({
                'error': 'Permission denied. Admin access required.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            user = User.objects.get(id=user_id)
            if user.is_superuser:
                return Response({
                    'error': 'Cannot delete superuser.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user.delete()
            return Response({
                'message': 'User deleted successfully.'
            }, status=status.HTTP_200_OK)
        
        except User.DoesNotExist:
            return Response({
                'error': 'User not found.'
            }, status=status.HTTP_404_NOT_FOUND)

# Google OAuth (placeholder for future implementation)
class GoogleAuthView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        # This will be implemented with Google OAuth integration
        return Response({
            'message': 'Google authentication will be implemented soon.'
        }, status=status.HTTP_501_NOT_IMPLEMENTED)