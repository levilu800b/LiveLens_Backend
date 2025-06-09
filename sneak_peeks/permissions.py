# sneak_peeks/permissions.py
# type: ignore

from rest_framework import permissions

class IsAuthorOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow authors of a sneak peek to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.READONLY_METHODS:
            return True
        
        # Write permissions are only allowed to the author of the sneak peek or admin
        return obj.author == request.user or request.user.is_admin


class IsCreatorOrReadOnly(permissions.BasePermission):
    """
    Custom permission for playlists - only allow creators to edit.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions for public playlists or own playlists
        if request.method in permissions.READONLY_METHODS:
            return obj.is_public or obj.creator == request.user or request.user.is_admin
        
        # Write permissions only for creator or admin
        return obj.creator == request.user or request.user.is_admin