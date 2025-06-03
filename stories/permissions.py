# type: ignore

# stories/permissions.py
from rest_framework import permissions

class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Permission to only allow authors of a story to edit it.
    Admins can edit any story.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Check if user is admin
        if hasattr(request.user, 'is_admin') and request.user.is_admin():
            return True
        
        # Write permissions are only given to the author of the story
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


