from rest_framework import permissions

from .helpers import is_customer


class ManagerAllCustomerAndDeliveryCrewReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False

        if request.user.is_superuser:
            return True

        if request.method in permissions.SAFE_METHODS:
            return True

        if request.user.groups.filter(name="Manager").exists():
            return True

        return False


class ManagerOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True
        return request.user.groups.filter(name="Manager").exists()


class OrderListPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        if request.user.is_superuser:
            return True

        if request.method == "POST" and not is_customer(request.user):
            return False

        return True
