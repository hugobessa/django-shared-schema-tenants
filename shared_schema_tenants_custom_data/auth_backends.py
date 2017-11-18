import sys
from shared_schema_tenants.auth_backends import TenantModelBackend
from shared_schema_tenants.helpers.tenants import get_current_tenant
from shared_schema_tenants_custom_data.models import (
    TenantSpecificTablesPermission, TenantSpecificTablesRelationship)


class TenantSpecificTablesBackend(TenantModelBackend):

    def _get_user_tenant_specific_tables_permissions(self, relationship):
        return relationship.permissions.all()

    def _get_group_tenant_specific_tables_permissions(self, relationship):
        relationship_groups_field = TenantSpecificTablesRelationship._meta.get_field('groups')
        relationship_groups_query = 'groups__%s' % relationship_groups_field.related_query_name()
        return TenantSpecificTablesPermission.objects.filter(**{relationship_groups_query: relationship})

    def _get_tenant_specific_tables_permissions(self, user_obj, obj, from_name):
        if not user_obj.is_active or user_obj.is_anonymous() or obj is not None:
            return set()

        tenant = get_current_tenant()
        if not tenant:
            return set()

        perm_cache_name = '_tenant_specific_tables_%s_perm_cache' % from_name

        if (not hasattr(user_obj, perm_cache_name) or
                not getattr(user_obj, perm_cache_name).get(tenant.pk)):
            if user_obj.is_superuser:
                relationship_perms = TenantSpecificTablesPermission.objects.all()
                relationship_perms = relationship_perms.values_list('codename', flat=True).order_by()
            else:
                try:
                    relationship = TenantSpecificTablesRelationship.objects.get(
                        user=user_obj, tenant=tenant)
                except TenantSpecificTablesRelationship.DoesNotExist:
                    relationship_perms = set()
                else:
                    relationship_perms = getattr(self, '_get_%s_tenant_specific_tables_permissions' %
                                                 from_name)(relationship)
                    relationship_perms = relationship_perms.values_list('codename', flat=True).order_by()
            setattr(user_obj, perm_cache_name, {
                tenant.pk: {
                    name for name in relationship_perms
                }
            })
        return getattr(user_obj, perm_cache_name).get(tenant.pk)

    def get_user_tenant_specific_tables_permissions(self, user_obj, obj=None):
        return self._get_tenant_specific_tables_permissions(user_obj, obj, 'user')

    def get_group_tenant_specific_tables_permissions(self, user_obj, obj=None):
        return self._get_tenant_specific_tables_permissions(user_obj, obj, 'group')

    def get_all_tenant_specific_table_permissions(self, user_obj, obj=None):
        if not user_obj.is_active or user_obj.is_anonymous() or obj is not None:
            return set()

        tenant = get_current_tenant()
        if not tenant:
            return set()

        self.has_module_perms

        if (not hasattr(user_obj, '_tenant_specific_tables_perm_cache') or
                not getattr(user_obj, '_tenant_specific_tables_perm_cache').get(tenant.pk)):

            user_obj._tenant_specific_tables_perm_cache = {
                tenant.pk: self.get_user_tenant_specific_tables_permissions(user_obj, obj)}

            user_obj._tenant_specific_tables_perm_cache[tenant.pk] = (
                user_obj._tenant_specific_tables_perm_cache[tenant.pk].union(
                    self.get_group_tenant_specific_tables_permissions(user_obj, obj))
            )

        return user_obj._tenant_specific_tables_perm_cache[tenant.pk]

    def has_perm(self, user_obj, perm, obj=None):
        custom_table_perm_types = [str]

        if sys.version_info < (3,0,0):
            custom_table_perm_types = [str, unicode]

        if type(perm) in custom_table_perm_types:
            return perm in self.get_all_tenant_specific_table_permissions(user_obj, obj)

        if not user_obj.is_active:
            return False
        return perm in self.get_all_permissions(user_obj, obj)
