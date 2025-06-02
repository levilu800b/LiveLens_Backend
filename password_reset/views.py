# type: ignore

# password_reset/views.py
from rest_framework import generics, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db import transaction
from authapp.utils import send_password_reset_email
from .models import PasswordResetCode
from .serializers import (
    PasswordResetRequestSerializer, 
    PasswordResetVerifySerializer,
    PasswordResetConfirmSerializer
)


class PasswordResetRequestView(generics.GenericAPIView):
    serializer_class = PasswordResetRequestSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data['email']
        user = User.objects.get(email=email)
        
        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        
        # Create reset code
        reset_code = PasswordResetCode.objects.create(
            user=user,
            ip_address=ip
        )
        
        # Send email
        send_password_reset_email(user.email, reset_code.code)
        
        return Response({
            'message': 'Password reset code sent to your email.'
        }, status=status.HTTP_200_OK)


class PasswordResetVerifyView(generics.GenericAPIView):
    serializer_class = PasswordResetVerifySerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        return Response({
            'message': 'Reset code verified successfully. You can now set a new password.'
        }, status=status.HTTP_200_OK)


class PasswordResetConfirmView(generics.GenericAPIView):
    serializer_class = PasswordResetConfirmSerializer
    permission_classes = [AllowAny]
    
    def post(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        reset_code = serializer.validated_data['reset_code']
        new_password = serializer.validated_data['new_password']
        
        with transaction.atomic():
            # Update password
            user.set_password(new_password)
            user.save()
            
            # Mark reset code as used
            reset_code.is_used = True
            reset_code.save()
        
        return Response({
            'message': 'Password reset successfully. You can now log in with your new password.'
        }, status=status.HTTP_200_OK)
