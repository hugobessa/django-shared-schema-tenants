from rest_framework.permissions import DjangoModelPermissions
from rest_framework import exceptions
from shared_schema_tenants_custom_data.models import TenantSpecificTable


class DjangoTenantSpecificTablePermissions(DjangoModelPermissions):
    tenant_specific_tables_perms_map = {
        'GET': [],
        'OPTIONS': [],
        'HEAD': [],
        'POST': ['add_%(model_name)s'],
        'PUT': ['change_%(model_name)s'],
        'PATCH': ['change_%(model_name)s'],
        'DELETE': ['delete_%(model_name)s'],
    }

    authenticated_users_only = True

    def get_required_permissions(self, method, table_id):
        """
        Given a model and an HTTP method, return the list of permission
        codes that the user is required to have.
        """
        table = TenantSpecificTable.objects.get(id=table_id)

        kwargs = {
            'model_name': table.name,
        }

        if method not in self.perms_map:
            raise exceptions.MethodNotAllowed(method)

        return [perm % kwargs for perm in self.tenant_specific_tables_perms_map[method]]

    def _queryset(self, view):
        assert hasattr(view, 'get_queryset') \
            or getattr(view, 'queryset', None) is not None, (
            'Cannot apply {} on a view that does not set '
            '`.queryset` or have a `.get_queryset()` method.'
        ).format(self.__class__.__name__)

        if hasattr(view, 'get_queryset'):
            queryset = view.get_queryset()
            assert queryset is not None, (
                '{}.get_queryset() returned None'.format(view.__class__.__name__)
            )
            return queryset
        return view.queryset

    def has_permission(self, request, view):
        if getattr(view, '_ignore_model_permissions', False):
            return True

        if not request.user or (
           not request.user.is_authenticated and self.authenticated_users_only):
            return False

        queryset = self._queryset(view)
        perms = self.get_required_permissions(request.method, queryset.table_id)

        return request.user.has_perms(perms)
