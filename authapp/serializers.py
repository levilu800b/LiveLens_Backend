#type: ignore
# authapp/serializers.py


from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.password_validation import validate_password
from .models import User, EmailVerification, UserActivity, UserLibrary, UserFavorites


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'password', 'password_confirm']
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Password fields didn't match.")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class EmailVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=6)
    
    def validate(self, attrs):
        email = attrs.get('email')
        code = attrs.get('code')
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("User with this email does not exist.")
        
        verification = EmailVerification.objects.filter(
            user=user, 
            code=code, 
            is_used=False
        ).first()
        
        if not verification:
            raise serializers.ValidationError("Invalid verification code.")
        
        if verification.is_expired():
            raise serializers.ValidationError("Verification code has expired.")
        
        attrs['user'] = user
        attrs['verification'] = verification
        return attrs


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(username=email, password=password)
            if not user:
                raise serializers.ValidationError("Invalid login credentials.")
            
            if not user.is_verified:
                raise serializers.ValidationError("Please verify your email before logging in.")
            
            attrs['user'] = user
        else:
            raise serializers.ValidationError("Must include email and password.")
        
        return attrs


class UserProfileSerializer(serializers.ModelSerializer):
    full_name = serializers.ReadOnlyField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'username', 'first_name', 'last_name', 'full_name',
            'phone_number', 'gender', 'country', 'date_of_birth', 'avatar',
            'is_admin', 'is_verified', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'email', 'is_admin', 'is_verified', 'created_at', 'updated_at']


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone_number', 'gender', 'country', 'date_of_birth', 'avatar']


class UserActivitySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = UserActivity
        fields = ['id', 'user_name', 'activity_type', 'content_type', 'content_id', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserLibrarySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = UserLibrary
        fields = ['id', 'user_name', 'content_type', 'content_id', 'added_at', 'last_accessed', 'progress']
        read_only_fields = ['id', 'user_name', 'added_at']


class UserFavoritesSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = UserFavorites
        fields = ['id', 'user_name', 'content_type', 'content_id', 'added_at']
        read_only_fields = ['id', 'user_name', 'added_at']


class PasswordChangeSerializer(serializers.Serializer):
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError("New password fields didn't match.")
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value