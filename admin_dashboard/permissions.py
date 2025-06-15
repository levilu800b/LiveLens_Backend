# ===================================================================
# admin_dashboard/permissions.py (Optional - for additional custom permissions)
# type: ignore
# ===================================================================

from rest_framework import permissions

class IsSuperAdminPermission(permissions.BasePermission):
    """
    Custom permission to only allow superuser access to certain endpoints
    """
    
    def has_permission(self, request, view):
        return (request.user and 
                request.user.is_authenticated and 
                request.user.is_superuser)


class IsAdminOrReadOnlyPermission(permissions.BasePermission):
    """
    Custom permission to allow admin users full access,
    but regular staff users only read access
    """
    
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated and request.user.is_staff):
            return False
        
        # Superusers have full access
        if request.user.is_superuser:
            return True
        
        # Staff users can only read
        if request.method in permissions.SAFE_METHODS:
            return True
        
        return False
