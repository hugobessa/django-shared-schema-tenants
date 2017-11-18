import mock
from django.test import RequestFactory
from model_mommy import mommy

from tests.utils import SharedSchemaTenantsTestCase
from shared_schema_tenants.permissions import DjangoTenantModelPermissions

try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse


class DjangoTenantModelPermissionsTests(SharedSchemaTenantsTestCase):

    def setUp(self):
        super(DjangoTenantModelPermissionsTests, self).setUp()
        factory = RequestFactory()
        self.request = factory.post(reverse('shared_schema_tenants:tenant_list'))
        self.request.user = self.user
        self.permission = DjangoTenantModelPermissions()

    def test_has_object_permission_with_created_tenant_single_tenant_object(self):
        obj = mock.Mock(spec=['tenant'])
        obj.tenant = self.tenant
        self.assertTrue(self.permission.has_object_permission(self.request, None, obj))

    def test_has_object_permission_with_created_tenant_multi_tenant_object(self):
        obj = mock.Mock(spec=['tenants'])
        obj.tenants = mock.Mock(spec=['all'])
        obj.tenants.all = lambda: [self.tenant]
        self.assertTrue(self.permission.has_object_permission(self.request, None, obj))

    def test_has_object_permission_with_new_tenant_single_tenant_object(self):
        obj = mock.Mock(spec=['tenant'])
        obj.tenant = mommy.make('shared_schema_tenants.Tenant')
        self.assertFalse(self.permission.has_object_permission(self.request, None, obj))

    def test_has_object_permission_with_new_tenant_multi_tenant_object(self):
        obj = mock.Mock(spec=['tenants'])
        obj.tenants = mock.Mock(spec=['all'])
        obj.tenants.all = lambda: [mommy.make('shared_schema_tenants.Tenant')]
        self.assertFalse(self.permission.has_object_permission(self.request, None, obj))

    def test_has_object_permission_without_tenant_attributes(self):
        obj = mock.Mock(spec=['test_not_tenant_attribute'])
        self.assertTrue(self.permission.has_object_permission(self.request, None, obj))
