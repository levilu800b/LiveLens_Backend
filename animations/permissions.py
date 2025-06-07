# type: ignore

# animations/permissions.py
from rest_framework import permissions

class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Permission to only allow authors of an animation to edit it.
    Admins can edit any animation.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if user is admin
        if hasattr(request.user, 'is_admin') and request.user.is_admin():
            return True
        
        # Write permissions are only given to the author of the animation
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
        return obj.user == request.user or obj.creator == request.user

class IsPremiumUser(permissions.BasePermission):
    """
    Permission to only allow premium users to access premium content.
    """
    
    def has_object_permission(self, request, view, obj):
        # If animation is not premium, allow access
        if not getattr(obj, 'is_premium', False):
            return True
        
        # If user is not authenticated, deny access
        if not request.user.is_authenticated:
            return False
        
        # Check if user has premium access
        return getattr(request.user, 'is_premium', False) or request.user.is_superuser

class CanAccessVideo(permissions.BasePermission):
    """
    Permission to check if user can access video content.
    """
    
    def has_permission(self, request, view):
        # Only authenticated users can access video files
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Check premium access
        if getattr(obj, 'is_premium', False):
            return (getattr(request.user, 'is_premium', False) or 
                   request.user.is_superuser or 
                   obj.author == request.user)
        
        return True

class CanGenerateAI(permissions.BasePermission):
    """
    Permission to check if user can generate AI animations.
    """
    
    def has_permission(self, request, view):
        # Only authenticated users can generate AI animations
        if not request.user.is_authenticated:
            return False
        
        # Check if user has AI generation privileges
        # This could be based on subscription level, admin status, etc.
        return (getattr(request.user, 'is_premium', False) or 
               getattr(request.user, 'is_admin', False) or 
               request.user.is_superuser)

class CanViewAIRequests(permissions.BasePermission):
    """
    Permission to view AI animation requests.
    """
    
    def has_permission(self, request, view):
        return request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        # Users can only view their own AI requests, admins can view all
        if hasattr(request.user, 'is_admin') and request.user.is_admin():
            return True
        
        return obj.user == request.user