from rest_framework.permissions import DjangoModelPermissions


class DjangoTenantModelPermissions(DjangoModelPermissions):

    def has_object_permission(self, request, view, obj):
        if hasattr(obj, 'tenant'):
            kwargs = {'tenant': obj.tenant}
        elif hasattr(obj, 'tenants'):
            kwargs = {'tenant__in': obj.tenants.all()}
        else:
            return False

        return request.user.relationships.filter(**kwargs).exists()
