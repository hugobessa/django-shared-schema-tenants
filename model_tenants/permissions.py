from rest_framework import permissions
from django.utils.translation import ugettext_lazy as _

from plans.permissions import system_access_permission_factory


class DjangoTenantModelPermission(permissions.DjangoModelPermissions):

    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }

    def has_permission(self, request, view):
        from model_tenants.middleware import TenantMiddleware
        tenant = TenantMiddleware.get_current_tenant()
        return super().has_permission(request, view) \
            and tenant != None \
            and request.user.relationships.filter(tenant=tenant).exists()

    def has_object_permission(self, request, view, obj):
        return request.user.relationships.filter(tenant=obj.tenant).exists()


class DjangoTenantModelSystemAccessBasePermission(DjangoTenantModelPermission):
    system_permissions_required = []
    perms_map = {
        'GET': ['%(app_label)s.view_%(model_name)s'],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['%(app_label)s.add_%(model_name)s'],
        'PUT': ['%(app_label)s.change_%(model_name)s'],
        'PATCH': ['%(app_label)s.change_%(model_name)s'],
        'DELETE': ['%(app_label)s.delete_%(model_name)s'],
    }

    def has_permission(self, request, view):

        if super().has_permission(request, view):
            return True

        else:
            SystemAccessPermission = system_access_permission_factory(
                self.system_permissions_required)
            return SystemAccessPermission().has_permission(request, view)


def django_tenant_model_system_access_permission_factory(permissions_required):

    class DjangoTenantModelSystemAccessPermissions(DjangoTenantModelSystemAccessBasePermission):
        def __init__(self, *args, **kwargs):
            self.system_permissions_required = permissions_required
            super().__init__(*args, **kwargs)

    return DjangoTenantModelSystemAccessPermissions
