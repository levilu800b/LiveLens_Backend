# type: ignore

# password_reset/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import PasswordResetRequest
from authapp.utils import send_password_reset_email

User = get_user_model()

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("No account found with this email address.")
        return value
    
    def save(self, **kwargs):
        email = self.validated_data['email']
        user = User.objects.get(email=email)
        
        # Invalidate existing reset requests for this email
        PasswordResetRequest.objects.filter(
            email=email,
            is_used=False
        ).update(is_used=True)
        
        # Create new reset request
        reset_request = PasswordResetRequest.objects.create(
            email=email,
            ip_address=kwargs.get('ip_address'),
            user_agent=kwargs.get('user_agent', '')
        )
        
        # Send reset email
        send_password_reset_email(user, reset_request.reset_code)
        
        return reset_request

class PasswordResetVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    reset_code = serializers.CharField(max_length=6)
    
    def validate(self, attrs):
        email = attrs.get('email')
        reset_code = attrs.get('reset_code')
        
        try:
            reset_request = PasswordResetRequest.objects.get(
                email=email,
                reset_code=reset_code
            )
        except PasswordResetRequest.DoesNotExist:
            raise serializers.ValidationError("Invalid reset code.")
        
        if not reset_request.is_valid():
            raise serializers.ValidationError("Reset code has expired or been used.")
        
        attrs['reset_request'] = reset_request
        return attrs

class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    reset_code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        
        email = attrs.get('email')
        reset_code = attrs.get('reset_code')
        
        try:
            reset_request = PasswordResetRequest.objects.get(
                email=email,
                reset_code=reset_code
            )
        except PasswordResetRequest.DoesNotExist:
            raise serializers.ValidationError("Invalid reset code.")
        
        if not reset_request.is_valid():
            raise serializers.ValidationError("Reset code has expired or been used.")
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
        
        attrs['reset_request'] = reset_request
        attrs['user'] = user
        return attrs
    
    def save(self):
        user = self.validated_data['user']
        reset_request = self.validated_data['reset_request']
        new_password = self.validated_data['new_password']
        
        # Update user password
        user.set_password(new_password)
        user.save()
        
        # Mark reset request as used
        reset_request.mark_as_used()
        
        return user