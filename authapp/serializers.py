#type: ignore
# authapp/serializers.py

from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, EmailVerificationCode, UserPreferences
from .utils import send_verification_email

import logging
logger = logging.getLogger(__name__)

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('email', 'username', 'first_name', 'last_name', 'password', 'password_confirm')
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        
        # Create user preferences
        UserPreferences.objects.create(user=user)
        
        # Send verification email
        verification_code = EmailVerificationCode.objects.create(
            user=user,
            code_type='verification'
        )
        send_verification_email(user, verification_code.code)
        
        return user

class GoogleSignUpSerializer(serializers.Serializer):
    email = serializers.EmailField()
    first_name = serializers.CharField(max_length=30)
    last_name = serializers.CharField(max_length=30)
    google_id = serializers.CharField(max_length=100)
    avatar_url = serializers.URLField(required=False)
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def create(self, validated_data):
        avatar_url = validated_data.pop('avatar_url', None)
        
        # Generate a username from email
        username = validated_data['email'].split('@')[0]
        counter = 1
        original_username = username
        while User.objects.filter(username=username).exists():
            username = f"{original_username}{counter}"
            counter += 1
        
        user = User.objects.create_user(
            username=username,
            email=validated_data['email'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            google_id=validated_data['google_id'],
            is_verified=True,  # Google accounts are pre-verified
            password=None,  # No password for Google sign-up
            # ✅ FIXED: Initialize profile fields that might be missing
            phone_number='',
            gender='',
            country='',
            date_of_birth=None
        )
        
        # Create user preferences - IMPORTANT for profile functionality
        try:
            UserPreferences.objects.create(user=user)
        except Exception as e:
            logger.warning(f"Failed to create user preferences for Google user {user.id}: {e}")
        
        # Handle avatar URL if provided
        if avatar_url:
            try:
                # Download and save Google avatar
                import requests
                from django.core.files.base import ContentFile
                from django.core.files.storage import default_storage
                import uuid
                
                response = requests.get(avatar_url, timeout=10)
                if response.status_code == 200:
                    # Generate unique filename
                    file_extension = 'jpg'  # Default for Google avatars
                    filename = f"avatars/google_{user.id}_{uuid.uuid4().hex[:8]}.{file_extension}"
                    
                    # Save file
                    file_content = ContentFile(response.content)
                    saved_path = default_storage.save(filename, file_content)
                    user.avatar = saved_path
                    user.save()
                    
            except Exception as e:
                logger.warning(f"Failed to download Google avatar for user {user.id}: {e}")
                # Continue without avatar - not critical
        
        return user

class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    
    def validate(self, attrs):
        try:
            user = User.objects.get(email=attrs['email'])
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        
        try:
            verification_code = EmailVerificationCode.objects.get(
                user=user,
                code=attrs['code'],
                code_type='verification'
            )
        except EmailVerificationCode.DoesNotExist:
            raise serializers.ValidationError("Invalid verification code.")
        
        if not verification_code.is_valid():
            raise serializers.ValidationError("Verification code has expired or been used.")
        
        attrs['user'] = user
        attrs['verification_code'] = verification_code
        return attrs
    
    def save(self):
        user = self.validated_data['user']
        verification_code = self.validated_data['verification_code']
        
        user.is_verified = True
        user.save()
        
        verification_code.mark_as_used()
        return user

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField()
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            # Use email for authentication since USERNAME_FIELD = 'email'
            user = authenticate(username=email, password=password)
            
            if not user:
                raise serializers.ValidationError("Invalid credentials.")
            
            if not user.is_verified:
                raise serializers.ValidationError("Please verify your email before logging in.")
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError("Email and password are required.")

class GoogleLoginSerializer(serializers.Serializer):
    google_id = serializers.CharField(max_length=100)
    email = serializers.EmailField()
    
    def validate(self, attrs):
        try:
            user = User.objects.get(
                google_id=attrs['google_id'],
                email=attrs['email']
            )
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found. Please sign up first.")
        
        attrs['user'] = user
        return attrs

# authapp/serializers.py - Updated UserProfileSerializer

class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'phone_number', 'gender', 'country', 'date_of_birth', 'avatar', 'avatar_url',
            'is_verified', 'is_admin_user', 'created_at', 'updated_at'
        )
        read_only_fields = ('id', 'email', 'username', 'is_verified', 'is_admin_user', 'created_at', 'updated_at')
    
    def get_avatar_url(self, obj):
        """Return full avatar URL for local development"""
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None
    
    def to_representation(self, instance):
        """Convert backend field names to frontend field names for output"""
        data = super().to_representation(instance)
        
        # Map backend field names to frontend field names for output
        data['isAdmin'] = instance.is_admin_user or instance.is_superuser
        data['firstName'] = data.pop('first_name')
        data['lastName'] = data.pop('last_name')
        data['phoneNumber'] = data.pop('phone_number', None)
        data['dateOfBirth'] = data.pop('date_of_birth', None)
        data['isVerified'] = data.pop('is_verified')
        data['createdAt'] = data.pop('created_at')
        data['updatedAt'] = data.pop('updated_at')
        
        # Use avatar_url instead of avatar field
        data['avatar'] = data.pop('avatar_url', None)
        data.pop('avatar_url', None)  # Remove the extra field
        
        # Convert gender choice value back to display value for frontend
        gender_value = data.get('gender')
        if gender_value == 'M':
            data['gender'] = 'M'
        elif gender_value == 'F':
            data['gender'] = 'F'
        
        # Remove backend-specific field from response
        data.pop('is_admin_user', None)
        
        return data
class UserPreferencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPreferences
        fields = (
            'email_notifications', 'push_notifications', 'auto_play_videos',
            'preferred_video_quality', 'preferred_language', 'dark_mode'
        )

class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField()
    new_password = serializers.CharField(validators=[validate_password])
    new_password_confirm = serializers.CharField()
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
    
    def validate_old_password(self, value):
        if not self.user.check_password(value):
            raise serializers.ValidationError("Invalid old password.")
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New passwords don't match.")
        return attrs
    
    def save(self):
        self.user.set_password(self.validated_data['new_password'])
        self.user.save()
        return self.user

class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        
        if user.is_verified:
            raise serializers.ValidationError("User is already verified.")
        
        return value
    
    def save(self):
        user = User.objects.get(email=self.validated_data['email'])
        
        # Invalidate existing codes
        EmailVerificationCode.objects.filter(
            user=user,
            code_type='verification',
            is_used=False
        ).update(is_used=True)
        
        # Create new verification code
        verification_code = EmailVerificationCode.objects.create(
            user=user,
            code_type='verification'
        )
        
        send_verification_email(user, verification_code.code)
        return user