from django.contrib.auth.models import Group, Permission
from django.db import transaction
from shared_schema_tenants.settings import DEFAULT_TENANT_OWNER_PERMISSIONS


def get_current_tenant():
    from shared_schema_tenants.middleware import TenantMiddleware
    return TenantMiddleware.get_current_tenant()


def set_current_tenant(tenant_slug):
    from shared_schema_tenants.middleware import TenantMiddleware
    return TenantMiddleware.set_tenant(tenant_slug)


def clear_current_tenant():
    from shared_schema_tenants.middleware import TenantMiddleware
    return TenantMiddleware.clear_tenant()


def create_default_tenant_groups():
    with transaction.atomic():
        group, created = Group.objects.get_or_create(name='tenant_owner')

        if created:
            for perm in DEFAULT_TENANT_OWNER_PERMISSIONS:
                try:
                    group.permissions.add(Permission.objects.get(
                        content_type__app_label=perm.split('.')[0],
                        codename=perm.split('.')[1]))
                except Permission.DoesNotExist:
                    pass

        return [group]
