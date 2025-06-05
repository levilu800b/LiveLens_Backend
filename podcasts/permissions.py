# type: ignore

# podcasts/permissions.py
from rest_framework import permissions

class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Permission to only allow authors of a podcast to edit it.
    Admins can edit any podcast.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if user is admin
        if hasattr(request.user, 'is_admin') and request.user.is_admin():
            return True
        
        # Write permissions are only given to the author of the podcast
        return obj.author == request.user

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Permission to only allow admins to create/edit.
    Anyone can read.
    """
    
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return (request.user.is_authenticated and 
                hasattr(request.user, 'is_admin') and 
                request.user.is_admin())

class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any request
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only given to the owner
        return obj.user == request.user

class IsPremiumUser(permissions.BasePermission):
    """
    Permission to only allow premium users to access premium content.
    """
    
    def has_object_permission(self, request, view, obj):
        # If content is not premium, allow access
        if not getattr(obj, 'is_premium', False):
            return True
        
        # If user is not authenticated, deny access
        if not request.user.is_authenticated:
            return False
        
        # Check if user has premium access
        return getattr(request.user, 'is_premium', False) or request.user.is_superuser

class CanAccessAudio(permissions.BasePermission):
    """
    Permission to check if user can access audio content.
    """
    
    def has_permission(self, request, view):
        # Only authenticated users can access audio files
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Check premium access for episodes
        if getattr(obj, 'is_premium', False):
            return (getattr(request.user, 'is_premium', False) or 
                   request.user.is_superuser or 
                   obj.author == request.user)
        
        return True

class IsSubscribed(permissions.BasePermission):
    """
    Permission to check if user is subscribed to a podcast series.
    """
    
    def has_object_permission(self, request, view, obj):
        # If user is not authenticated, deny access
        if not request.user.is_authenticated:
            return False
        
        # Check if user is subscribed to the series
        from .models import PodcastSubscription
        
        # For episodes, check subscription to the series
        if hasattr(obj, 'series'):
            return PodcastSubscription.objects.filter(
                user=request.user,
                series=obj.series
            ).exists()
        
        # For series, check direct subscription
        return PodcastSubscription.objects.filter(
            user=request.user,
            series=obj
        ).exists()