from rest_framework import permissions


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object.
        return obj.owner_username == request.user.username


class IsMomentMember(permissions.BasePermission):
    """
    Custom permission to only allow members of a moment to access it.
    """
    
    def has_object_permission(self, request, view, obj):
        # Check if user is the owner or a member
        if hasattr(obj, 'owner_username'):
            return (obj.owner_username == request.user.username or 
                    request.user.username in (obj.allowed_usernames or []))
        return False


class IsOwnerOrMember(permissions.BasePermission):
    """
    Custom permission to allow owners and members to access moments.
    """
    
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated
    
    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'owner_username'):
            return (obj.owner_username == request.user.username or 
                    request.user.username in (obj.allowed_usernames or []))
        return False
