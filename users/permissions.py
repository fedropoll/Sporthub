from rest_framework import permissions
from rest_framework.permissions import BasePermission, SAFE_METHODS
from .models import UserRole

class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_staff:
            return True
        return obj.user == request.user


class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True
        if request.user and request.user.is_staff:
            return True
        return obj.user == request.user


class IsAdmin(permissions.BasePermission):
    """
    Разрешение только для администраторов
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'userprofile') and 
            request.user.userprofile.role == UserRole.ADMIN
        )


class IsTrainer(permissions.BasePermission):
    """
    Разрешение только для тренеров
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'userprofile') and 
            request.user.userprofile.role == UserRole.TRAINER
        )


class IsUser(permissions.BasePermission):
    """
    Разрешение только для обычных пользователей
    """
    def has_permission(self, request, view):
        return bool(
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'userprofile') and 
            request.user.userprofile.role == UserRole.USER
        )


class IsAdminOrTrainer(permissions.BasePermission):
    """
    Разрешение для администраторов и тренеров
    """
    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False
            
        if not hasattr(request.user, 'userprofile'):
            return False
            
        return request.user.userprofile.role in [UserRole.ADMIN, UserRole.TRAINER]


class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Разрешение на чтение для всех, на изменение только для администраторов
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
            
        return bool(
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'userprofile') and 
            request.user.userprofile.role == UserRole.ADMIN
        )
