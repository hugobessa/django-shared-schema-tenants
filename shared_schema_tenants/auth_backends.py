from django.contrib.auth.models import Permission
from django.contrib.auth.backends import ModelBackend

from django.contrib.auth import get_user_model
UserModel = get_user_model()

import logging
logger = logging.getLogger(__name__)

from shared_schema_tenants.models import Tenant, TenantRelationship
from shared_schema_tenants.helpers.tenants import get_current_tenant


class TenantModelBackend(ModelBackend):
    """
    Authenticates against settings.AUTH_USER_MODEL.
    """

    def _get_user_permissions(self, relationship):
        return relationship.permissions.all()

    def _get_group_permissions(self, relationship):
        relationship_groups_field = TenantRelationship._meta.get_field(
            'groups')
        relationship_groups_query = 'group__%s' % relationship_groups_field.related_query_name()
        return Permission.objects.filter(**{relationship_groups_query: relationship})

    def _get_permissions(self, user_obj, obj, from_name):
        """
        Return the permissions of `user_obj` from `from_name`. `from_name` can
        be either "group" or "user" to return permissions from
        `_get_group_permissions` or `_get_user_permissions` respectively.
        """
        tenant = get_current_tenant()
        if tenant == None: return set()

        if not user_obj.is_active or user_obj.is_anonymous or obj is not None:
            return set()

        perm_cache_name = '_%s_perm_cache' % from_name

        if not hasattr(user_obj, perm_cache_name):
            if user_obj.is_superuser:
                perms = Permission.objects.all()
            else:
                try:
                    tenant_relationship = TenantRelationship.objects.get(
                        user=user_obj, tenant=tenant)
                    perms = getattr(self, '_get_%s_permissions' %
                                    from_name)(tenant_relationship)
                except TenantRelationship.DoesNotExist:
                    perms = Permission.objects.none()

            perms = perms.values_list('content_type__app_label', 'codename').order_by()
            setattr(tenant_relationship, perm_cache_name, {
                    "%s.%s" % (ct, name) for ct, name in perms})
        return getattr(tenant_relationship, perm_cache_name)



    def get_all_permissions(self, user_obj, obj=None):
        if not user_obj.is_active or user_obj.is_anonymous or obj is not None:
            return set()
        try:
            tenant = get_current_tenant()
            if tenant == None: return set()
            relationship = TenantRelationship.objects.get(
                user=user_obj, tenant=tenant)
        except TenantRelationship.DoesNotExist:
            return set()

        if not hasattr(relationship, '_perm_cache'):
            relationship._perm_cache = self.get_user_permissions(
                user_obj)
            relationship._perm_cache.update(
                self.get_group_permissions(user_obj))
            user_obj._perm_cache = relationship._perm_cache
        return relationship._perm_cache


try:
    from allauth.account import app_settings
    from allauth.account.app_settings import AuthenticationMethod
    from allauth.account.utils import filter_users_by_email, filter_users_by_username

    class TenantAuthenticationBackend(TenantModelBackend):

        def authenticate(self, **credentials):
            ret = None
            if app_settings.AUTHENTICATION_METHOD == AuthenticationMethod.EMAIL:
                ret = self._authenticate_by_email(**credentials)
            elif app_settings.AUTHENTICATION_METHOD \
                    == AuthenticationMethod.USERNAME_EMAIL:
                ret = self._authenticate_by_email(**credentials)
                if not ret:
                    ret = self._authenticate_by_username(**credentials)
            else:
                ret = self._authenticate_by_username(**credentials)
            return ret

        def _authenticate_by_username(self, **credentials):
            username_field = app_settings.USER_MODEL_USERNAME_FIELD
            username = credentials.get('username')
            password = credentials.get('password')

            User = get_user_model()

            if not username_field or username is None or password is None:
                return None
            try:
                # Username query is case insensitive
                user = filter_users_by_username(username).get()

                if user.check_password(password):
                    tenant = get_current_tenant()
                    if tenant == None: return set()
                    if (user.relationships.filter(tenant=tenant).exists()
                            or user.is_superuser):
                        return user
                return None
            except User.DoesNotExist:
                return None


        def _authenticate_by_email(self, **credentials):
            # Even though allauth will pass along `email`, other apps may
            # not respect this setting. For example, when using
            # django-tastypie basic authentication, the login is always
            # passed as `username`.  So let's place nice with other apps
            # and use username as fallback
            email = credentials.get('email', credentials.get('username'))
            if email:
                for user in filter_users_by_email(email):
                    if user.check_password(credentials["password"]):
                        tenant = get_current_tenant()
                        if tenant == None: return set()
                        if (user.relationships.filter(tenant=tenant).exists()
                                or user.is_superuser):
                            return user
            return None

except ImportError:

    class TenantAuthenticationBackend(TenantModelBackend):
        def __init__(self, *args, **kwargs):
            logger.error('allauth needs to be added to INSTALLED_APPS.')
            super(TenantAuthenticationBackend, self).__init__(*args, **kwargs)
