from rest_framework.permissions import BasePermission
from .models import UserRole, Role

class HasTenantRolePermission(BasePermission):
    """
    Permission class that checks if the requesting user's assigned roles within the tenant
    contain the required permission code (e.g. 'crm.read', 'finance.admin').
    """
    required_permission = None

    def __init__(self, required_permission=None):
        if required_permission:
            self.required_permission = required_permission

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # Superusers and company admins have full platform access
        if request.user.is_superuser or request.user.is_staff:
            return True

        if not hasattr(request.user, 'profile') or not request.user.profile.company:
            return False

        # If no specific permission required on the view, authenticated tenant user passes
        perm_code = getattr(view, 'required_permission', self.required_permission)
        if not perm_code:
            return True

        # Check assigned roles
        user_profile = request.user.profile
        assigned_roles = Role.objects.filter(
            company=user_profile.company,
            assigned_users__user_profile=user_profile
        )

        for role in assigned_roles:
            perms = role.permissions or []
            if '*' in perms or 'admin' in perms or perm_code in perms:
                return True

        # If user has no custom roles yet, allow basic access if not explicitly restricted
        if not assigned_roles.exists():
            return True

        return False


class IsTenantAdmin(BasePermission):
    """
    Ensures the user has an Admin role in their tenant or is superuser/staff.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        if request.user.is_superuser or request.user.is_staff:
            return True

        if not hasattr(request.user, 'profile') or not request.user.profile.company:
            return False

        user_profile = request.user.profile
        admin_roles = Role.objects.filter(
            company=user_profile.company,
            assigned_users__user_profile=user_profile,
            name__iexact='admin'
        )
        return admin_roles.exists()
