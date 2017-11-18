from django.test import TestCase
from django.contrib.auth.models import User, Permission

from shared_schema_tenants.helpers.tenant_relationships import create_relationship
from shared_schema_tenants.helpers.tenants import (
    create_default_tenant_groups, set_current_tenant, clear_current_tenant)
from shared_schema_tenants.models import Tenant
from shared_schema_tenants.auth_backends import TenantModelBackend


class TenantModelBackendTests(TestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(name='test', slug='test')
        set_current_tenant(self.tenant.slug)
        self.user = User.objects.create_user(
            first_name='test', last_name='test',
            username='test', email='test@sharedschematenants.com',
            password='test')
        self.relationship = create_relationship(self.tenant, self.user,
                                                groups=create_default_tenant_groups())

    def test__get_group_tenant_permissions(self):
        set_current_tenant(self.tenant.slug)
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend._get_tenant_permissions(self.user, None, 'group')),
            self.relationship.groups.first().permissions.count()
        )
        self.assertEqual(
            len(self.user._tenant_group_perm_cache[self.tenant.pk]),
            self.relationship.groups.first().permissions.count()
        )

    def test__get_user_tenant_permissions(self):
        set_current_tenant(self.tenant.slug)
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend._get_tenant_permissions(self.user, None, 'user')),
            self.relationship.permissions.count()
        )
        self.assertEqual(
            len(self.user._tenant_user_perm_cache[self.tenant.pk]),
            self.relationship.permissions.count()
        )

    def test__get_permissions(self):
        set_current_tenant(self.tenant.slug)
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend._get_permissions(self.user, None, 'group')),
            self.relationship.groups.first().permissions.count()
        )

    def test_get_all_tenant_permissions(self):
        set_current_tenant(self.tenant.slug)
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend.get_all_tenant_permissions(self.user)),
            self.relationship.groups.first().permissions.count()
        )
        self.assertEqual(
            len(self.user._tenant_perm_cache[self.tenant.pk]),
            self.relationship.groups.first().permissions.count()
        )

    def test_get_all_permissions(self):
        set_current_tenant(self.tenant.slug)
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend.get_all_permissions(self.user)),
            self.relationship.groups.first().permissions.count()
        )
        self.assertEqual(
            len(self.user._tenant_perm_cache[self.tenant.pk]),
            self.relationship.groups.first().permissions.count()
        )

    def test__get_user_permissions(self):
        set_current_tenant(self.tenant.slug)
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend._get_user_permissions(self.relationship)),
            self.relationship.permissions.count()
        )

    def test__get_group_permissions(self):
        set_current_tenant(self.tenant.slug)
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend._get_group_permissions(self.relationship)),
            self.relationship.groups.first().permissions.count()
        )

    def test__get_group_tenant_permissions_with_superuser(self):
        set_current_tenant(self.tenant.slug)
        self.user.is_superuser = True
        self.user.save()
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend._get_tenant_permissions(self.user, None, 'group')),
            Permission.objects.all().count()
        )
        self.assertEqual(
            len(self.user._tenant_group_perm_cache[self.tenant.pk]),
            Permission.objects.all().count()
        )

    def test__get_user_tenant_permissions_with_superuser(self):
        set_current_tenant(self.tenant.slug)
        self.user.is_superuser = True
        self.user.save()
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend._get_tenant_permissions(self.user, None, 'user')),
            Permission.objects.all().count()
        )
        self.assertEqual(
            len(self.user._tenant_user_perm_cache[self.tenant.pk]),
            Permission.objects.all().count()
        )

    def test__get_permissions_with_superuser(self):
        set_current_tenant(self.tenant.slug)
        self.user.is_superuser = True
        self.user.save()
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend._get_permissions(self.user, None, 'group')),
            Permission.objects.all().count()
        )

    def test_get_all_tenant_permissions_with_superuser(self):
        set_current_tenant(self.tenant.slug)
        self.user.is_superuser = True
        self.user.save()
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend.get_all_tenant_permissions(self.user)),
            Permission.objects.all().count()
        )
        self.assertEqual(
            len(self.user._tenant_perm_cache[self.tenant.pk]),
            Permission.objects.all().count()
        )

    def test_get_all_permissions_with_superuser(self):
        set_current_tenant(self.tenant.slug)
        self.user.is_superuser = True
        self.user.save()
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend.get_all_permissions(self.user)),
            Permission.objects.all().count()
        )
        self.assertEqual(
            len(self.user._tenant_perm_cache[self.tenant.pk]),
            Permission.objects.all().count()
        )

    def test__get_group_tenant_permissions_without_tenant(self):
        clear_current_tenant()
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend._get_tenant_permissions(self.user, None, 'group')),
            0
        )

    def test__get_user_tenant_permissions_without_tenant(self):
        clear_current_tenant()
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend._get_tenant_permissions(self.user, None, 'user')),
            0
        )

    def test__get_permissions_without_tenant(self):
        clear_current_tenant()
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend._get_permissions(self.user, None, 'group')),
            0
        )

    def test_get_all_tenant_permissions_without_tenant(self):
        clear_current_tenant()
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend.get_all_tenant_permissions(self.user)),
            0
        )

    def test__get_group_tenant_permissions_without_active_user(self):
        set_current_tenant(self.tenant.slug)
        self.user.is_active = False
        self.user.save()
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend._get_tenant_permissions(self.user, None, 'group')),
            0
        )

    def test__get_user_tenant_permissions_without_active_user(self):
        set_current_tenant(self.tenant.slug)
        self.user.is_active = False
        self.user.save()
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend._get_tenant_permissions(self.user, None, 'user')),
            0
        )

    def test__get_permissions_without_active_user(self):
        set_current_tenant(self.tenant.slug)
        self.user.is_active = False
        self.user.save()
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend._get_permissions(self.user, None, 'group')),
            0
        )

    def test_get_all_tenant_permissions_without_active_user(self):
        set_current_tenant(self.tenant.slug)
        self.user.is_active = False
        self.user.save()
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend.get_all_tenant_permissions(self.user)),
            0
        )

    def test_get_all_permissions_without_active_user(self):
        set_current_tenant(self.tenant.slug)
        self.user.is_active = False
        self.user.save()
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend.get_all_permissions(self.user)),
            0
        )

    def test__get_group_tenant_permissions_without_user_in_tenant(self):
        set_current_tenant(self.tenant.slug)
        self.user.relationships.all().delete()
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend._get_tenant_permissions(self.user, None, 'group')),
            0
        )

    def test__get_user_tenant_permissions_without_user_in_tenant(self):
        set_current_tenant(self.tenant.slug)
        self.user.relationships.all().delete()
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend._get_tenant_permissions(self.user, None, 'user')),
            0
        )

    def test__get_permissions_without_user_in_tenant(self):
        set_current_tenant(self.tenant.slug)
        self.user.relationships.all().delete()
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend._get_permissions(self.user, None, 'group')),
            0
        )

    def test_get_all_tenant_permissions_without_user_in_tenant(self):
        set_current_tenant(self.tenant.slug)
        self.user.relationships.all().delete()
        auth_backend = TenantModelBackend()
        self.assertEqual(
            len(auth_backend.get_all_tenant_permissions(self.user)),
            0
        )
