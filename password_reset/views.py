# type: ignore

# password_reset/views.py
from rest_framework import status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from authapp.utils import log_user_activity

from .serializers import (
    PasswordResetRequestSerializer,
    PasswordResetVerifySerializer,
    PasswordResetConfirmSerializer
)

User = get_user_model()

class PasswordResetRequestView(APIView):
    """
    Request a password reset code
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetRequestSerializer(data=request.data)
        if serializer.is_valid():
            # Get IP address and user agent
            ip_address = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            reset_request = serializer.save(
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return Response({
                'message': 'Password reset code sent to your email address.',
                'email': reset_request.email
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class PasswordResetVerifyView(APIView):
    """
    Verify the password reset code
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetVerifySerializer(data=request.data)
        if serializer.is_valid():
            return Response({
                'message': 'Reset code verified successfully. You can now set a new password.',
                'valid': True
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetConfirmView(APIView):
    """
    Confirm password reset with new password
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Log the password reset activity
            log_user_activity(
                user, 
                'password_change', 
                'Password reset via email verification',
                request
            )
            
            return Response({
                'message': 'Password reset successfully. You can now log in with your new password.',
                'user_id': user.id
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class PasswordResetStatusView(APIView):
    """
    Check the status of recent password reset requests for an email
    """
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({
                'error': 'Email is required.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if user exists
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                'error': 'No account found with this email address.'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Check for recent reset requests
        from .models import PasswordResetRequest
        from django.utils import timezone
        from datetime import timedelta
        
        recent_requests = PasswordResetRequest.objects.filter(
            email=email,
            created_at__gte=timezone.now() - timedelta(hours=1)
        ).order_by('-created_at')
        
        if recent_requests.exists():
            latest_request = recent_requests.first()
            return Response({
                'has_recent_request': True,
                'latest_request_time': latest_request.created_at,
                'is_valid': latest_request.is_valid(),
                'expires_at': latest_request.expires_at
            }, status=status.HTTP_200_OK)
        
        return Response({
            'has_recent_request': False
        }, status=status.HTTP_200_OK)