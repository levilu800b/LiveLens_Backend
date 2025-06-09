# authapp/permissions.py
# type: ignore

from rest_framework import permissions

class IsAdminUser(permissions.BasePermission):
    """
    Custom permission to check if user is an admin.
    Checks both is_superuser and is_admin_user fields.
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_superuser or request.user.is_admin_user)
        )

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object or admins to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.READONLY_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object or admin
        return (
            obj.author == request.user or 
            obj.user == request.user or 
            request.user.is_superuser or 
            request.user.is_admin_user
        )

class IsAuthorOrAdmin(permissions.BasePermission):
    """
    Custom permission to only allow authors or admins to edit content.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        if request.method in permissions.READONLY_METHODS:
            return True
        
        # Write permissions only for author or admin
        return (
            obj.author == request.user or 
            request.user.is_superuser or 
            request.user.is_admin_user
        )

class CanViewDashboard(permissions.BasePermission):
    """
    Permission for dashboard access - admins and staff only
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_superuser or 
             request.user.is_admin_user or 
             request.user.is_staff)
        )

class CanManageContent(permissions.BasePermission):
    """
    Permission for content management - admins only
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            (request.user.is_superuser or request.user.is_admin_user)
        )

class CanManageUsers(permissions.BasePermission):
    """
    Permission for user management - superusers only
    """
    
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            request.user.is_superuser
        )