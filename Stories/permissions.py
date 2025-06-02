# type: ignore

# stories/permissions.py
from rest_framework import permissions


class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow authors of a story to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the author of the story.
        return obj.author == request.user


class IsAdminOrAuthor(permissions.BasePermission):
    """
    Custom permission to allow access to admins or the author.
    """
    
    def has_object_permission(self, request, view, obj):
        # Allow access to admins
        if request.user.is_admin:
            return True
        
        # Allow access to the author
        return obj.author == request.user