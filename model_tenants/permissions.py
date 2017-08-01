from rest_framework import permissions
from django.utils.translation import ugettext_lazy as _
from model_tenants.helpers.tenants import get_current_tenant


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
        tenant = get_current_tenant()
        return (
            super().has_permission(request, view)
                and tenant != None
                and request.user.relationships.filter(tenant=tenant).exists())

    def has_object_permission(self, request, view, obj):
        return request.user.relationships.filter(tenant=obj.tenant).exists()
