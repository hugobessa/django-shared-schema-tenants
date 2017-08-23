import logging
from django.contrib.auth.models import Permission
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

from shared_schema_tenants.models import TenantRelationship
from shared_schema_tenants.helpers.tenants import get_current_tenant


UserModel = get_user_model()

logger = logging.getLogger(__name__)


class TenantModelBackend(ModelBackend):
    """
    Authenticates against settings.AUTH_USER_MODEL.
    """

    def _get_user_global_permissions(self, user_obj):
        return user_obj.user_permissions.all()

    def _get_group_global_permissions(self, user_obj):
        user_groups_field = get_user_model()._meta.get_field('groups')
        user_groups_query = 'group__%s' % user_groups_field.related_query_name()
        return Permission.objects.filter(**{user_groups_query: user_obj})

    def _get_user_tenant_permissions(self, relationship):
        return relationship.permissions.all()

    def _get_group_tenant_permissions(self, relationship):
        relationship_groups_field = TenantRelationship._meta.get_field('groups')
        relationship_groups_query = 'group__%s' % relationship_groups_field.related_query_name()
        return Permission.objects.filter(**{relationship_groups_query: relationship})

    def _get_user_permissions(self, relationship):
        relationship_permissions_field = TenantRelationship._meta.get_field('permissions')
        relationship_permission_query = relationship_permissions_field.related_query_name()

        user_permissions_field = UserModel._meta.get_field('user_permissions')
        user_permission_query = user_permissions_field.related_query_name()

        user_groups_field = get_user_model()._meta.get_field('groups')
        user_groups_query = 'group__%s' % user_groups_field.related_query_name()
        return Permission.objects.filter(
            Q(**{relationship_permission_query: relationship}) |
            Q(**{user_permission_query: relationship.user}) |
            Q(**{user_groups_query: relationship.user})).distinct()

    def _get_group_permissions(self, relationship):
        relationship_groups_field = TenantRelationship._meta.get_field(
            'groups')
        relationship_groups_query = 'group__%s' % relationship_groups_field.related_query_name()
        user_groups_field = get_user_model()._meta.get_field('groups')
        user_groups_query = 'group__%s' % user_groups_field.related_query_name()
        return Permission.objects.filter(
            Q(**{relationship_groups_query: relationship}) |
            Q(**{user_groups_query: relationship.user}))

    def _get_tenant_permissions(self, user_obj, obj, from_name):
        if not user_obj.is_active or user_obj.is_anonymous() or obj is not None:
            return set()

        tenant = get_current_tenant()
        if not tenant:
            return set()

        perm_cache_name = '_tenant_%s_perm_cache' % from_name

        if (not hasattr(user_obj, perm_cache_name) or
                not getattr(user_obj, perm_cache_name).get(tenant.pk)):
            if user_obj.is_superuser:
                relationship_perms = Permission.objects.all()
                relationship_perms = relationship_perms.values_list(
                    'content_type__app_label', 'codename').order_by()
            else:
                try:
                    relationship = TenantRelationship.objects.get(
                        user=user_obj, tenant=tenant)
                except TenantRelationship.DoesNotExist:
                    relationship_perms = set()
                else:
                    relationship_perms = getattr(self, '_get_%s_tenant_permissions' %
                                                 from_name)(relationship)
                    relationship_perms = relationship_perms.values_list(
                        'content_type__app_label', 'codename').order_by()
            setattr(user_obj, perm_cache_name, {
                tenant.pk: {
                    "%s.%s" % (ct, name) for ct, name in relationship_perms
                }
            })

        return getattr(user_obj, perm_cache_name).get(tenant.pk)

    def _get_global_permissions(self, user_obj, obj, from_name):
        if not user_obj.is_active or user_obj.is_anonymous() or obj is not None:
            return set()

        perm_cache_name = '_%s_perm_cache' % from_name
        if not hasattr(user_obj, perm_cache_name):
            if user_obj.is_superuser:
                perms = Permission.objects.all()
            else:
                perms = getattr(self, '_get_%s_global_permissions' % from_name)(user_obj)
            perms = perms.values_list('content_type__app_label', 'codename').order_by()
            setattr(user_obj, perm_cache_name, set("%s.%s" % (ct, name) for ct, name in perms))
        return getattr(user_obj, perm_cache_name)

    def _get_permissions(self, user_obj, obj, from_name):
        return self._get_global_permissions(user_obj, obj, from_name).union(
            self._get_tenant_permissions(user_obj, obj, from_name))

    def get_user_global_permissions(self, user_obj, obj=None):
        return self._get_global_permissions(user_obj, obj, 'user')

    def get_user_tenant_permissions(self, user_obj, obj=None):
        return self._get_tenant_permissions(user_obj, obj, 'user')

    def get_group_global_permissions(self, user_obj, obj=None):
        return self._get_global_permissions(user_obj, obj, 'group')

    def get_group_tenant_permissions(self, user_obj, obj=None):
        return self._get_tenant_permissions(user_obj, obj, 'group')

    def get_all_global_permissions(self, user_obj, obj=None):
        if not user_obj.is_active or user_obj.is_anonymous() or obj is not None:
            return set()
        if not hasattr(user_obj, '_perm_cache'):
            user_obj._perm_cache = self.get_user_global_permissions(user_obj, obj)
            user_obj._perm_cache.update(self.get_group_global_permissions(user_obj, obj))
        return user_obj._perm_cache

    def get_all_tenant_permissions(self, user_obj, obj=None):
        if not user_obj.is_active or user_obj.is_anonymous() or obj is not None:
            return set()

        tenant = get_current_tenant()
        if not tenant:
            return set()

        if (not hasattr(user_obj, '_tenant_perm_cache') or
                not getattr(user_obj, '_tenant_perm_cache').get(tenant.pk)):
            user_obj._tenant_perm_cache = {tenant.pk: self.get_user_tenant_permissions(user_obj, obj)}
            user_obj._tenant_perm_cache[tenant.pk].update(self.get_group_tenant_permissions(user_obj, obj))
        return user_obj._tenant_perm_cache[tenant.pk]

    def get_all_permissions(self, user_obj, obj=None):
        return self.get_all_global_permissions(user_obj, obj).union(
            self.get_all_tenant_permissions(user_obj, obj))
