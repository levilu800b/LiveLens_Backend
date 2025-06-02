# type: ignore

# password_reset/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from .models import PasswordResetCode

User = get_user_model()


class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        return value


class PasswordResetVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    
    def validate(self, attrs):
        email = attrs.get('email')
        code = attrs.get('code')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        
        reset_code = PasswordResetCode.objects.filter(
            user=user, 
            code=code, 
            is_used=False
        ).first()
        
        if not reset_code:
            raise serializers.ValidationError("Invalid reset code.")
        
        if reset_code.is_expired():
            raise serializers.ValidationError("Reset code has expired.")
        
        attrs['user'] = user
        attrs['reset_code'] = reset_code
        return attrs


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Password fields didn't match.")
        
        email = attrs.get('email')
        code = attrs.get('code')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        
        reset_code = PasswordResetCode.objects.filter(
            user=user, 
            code=code, 
            is_used=False
        ).first()
        
        if not reset_code:
            raise serializers.ValidationError("Invalid reset code.")
        
        if reset_code.is_expired():
            raise serializers.ValidationError("Reset code has expired.")
        
        attrs['user'] = user
        attrs['reset_code'] = reset_code
        return attrs

