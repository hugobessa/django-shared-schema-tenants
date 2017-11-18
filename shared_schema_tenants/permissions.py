from rest_framework.permissions import BasePermission, DjangoModelPermissions


class DjangoTenantModelPermissions(DjangoModelPermissions):

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'tenant'):
            kwargs = {'tenant': obj.tenant}
        elif hasattr(obj, 'tenants'):
            kwargs = {'tenant__in': obj.tenants.all()}
        else:
            return True

        return request.user.relationships.filter(**kwargs).exists()


class IsTenantOwner(BasePermission):

    def has_permission(self, request, view):
        return (request.user.is_authenticated() and
                request.user.relationships.filter(groups__name="tenant_owner").exists())

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'tenant'):
            kwargs = {'tenant': obj.tenant}
        elif hasattr(obj, 'tenants'):
            kwargs = {'tenant__in': obj.tenants.all()}
        else:
            return True

        return (request.user.is_authenticated() and
                request.user.relationships.filter(**kwargs).exists())

