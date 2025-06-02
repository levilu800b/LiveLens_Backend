#type: ignore
# authapp/serializers.py


from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .models import User, EmailVerification, UserLibrary, UserFavorites
import random
import string

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'username', 'first_name', 'last_name', 
            'password', 'confirm_password'
        ]
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
        }
    
    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError("Passwords don't match.")
        return attrs
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value
    
    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return value
    
    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        
        # Generate verification code
        verification_code = ''.join(random.choices(string.digits, k=6))
        EmailVerification.objects.create(user=user, code=verification_code)
        
        return user

class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(style={'input_type': 'password'})
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            
            if not user:
                raise serializers.ValidationError('Invalid email or password.')
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            
            if not user.is_verified:
                raise serializers.ValidationError('Please verify your email before logging in.')
            
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include email and password.')

class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6, min_length=6)
    
    def validate(self, attrs):
        email = attrs.get('email')
        code = attrs.get('code')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError('User with this email does not exist.')
        
        verification = EmailVerification.objects.filter(
            user=user, code=code, is_used=False
        ).first()
        
        if not verification:
            raise serializers.ValidationError('Invalid verification code.')
        
        if verification.is_expired():
            raise serializers.ValidationError('Verification code has expired.')
        
        attrs['user'] = user
        attrs['verification'] = verification
        return attrs

class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    
    def validate_email(self, value):
        try:
            user = User.objects.get(email=value)
            if user.is_verified:
                raise serializers.ValidationError('User is already verified.')
        except User.DoesNotExist:
            raise serializers.ValidationError('User with this email does not exist.')
        return value

class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'phone_number', 'gender', 'country', 'date_of_birth', 'avatar',
            'is_verified', 'is_admin_user', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'email', 'is_verified', 'is_admin_user', 'created_at', 'updated_at']

class UserProfileUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'phone_number', 
            'gender', 'country', 'date_of_birth', 'avatar'
        ]
    
    def validate_phone_number(self, value):
        if value and User.objects.filter(phone_number=value).exclude(id=self.instance.id).exists():
            raise serializers.ValidationError("A user with this phone number already exists.")
        return value

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(style={'input_type': 'password'})
    new_password = serializers.CharField(style={'input_type': 'password'}, validators=[validate_password])
    confirm_new_password = serializers.CharField(style={'input_type': 'password'})
    
    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError("New passwords don't match.")
        return attrs

class UserLibrarySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLibrary
        fields = '__all__'
        read_only_fields = ['user', 'watched_at']

class UserLibraryCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserLibrary
        fields = ['content_type', 'content_id', 'is_completed', 'watch_progress']

class UserFavoritesSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFavorites
        fields = '__all__'
        read_only_fields = ['user', 'created_at']

class UserFavoritesCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFavorites
        fields = ['content_type', 'content_id']

class GoogleAuthSerializer(serializers.Serializer):
    token = serializers.CharField()
    
    def validate_token(self, value):
        # This will be implemented with Google OAuth validation
        # For now, we'll just validate that a token is provided
        if not value:
            raise serializers.ValidationError('Google token is required.')
        return value

class UserListSerializer(serializers.ModelSerializer):
    """Serializer for listing users (admin only)"""
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'is_active', 'is_verified', 'is_admin_user', 'created_at', 'last_login'
        ]