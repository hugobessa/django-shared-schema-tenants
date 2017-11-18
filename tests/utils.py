from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from model_mommy import mommy

from shared_schema_tenants.helpers.tenant_relationships import create_relationship
from shared_schema_tenants.helpers.tenants import (
    set_current_tenant, create_default_tenant_groups)


class SharedSchemaTenantsTestCase(TestCase):

    def setUp(self):
        self.tenant = mommy.make('shared_schema_tenants.Tenant')
        set_current_tenant(self.tenant.slug)
        self.user = User.objects.create_user(
            first_name='test', last_name='test',
            username='test', email='test@sharedschematenants.com',
            password='test')
        self.relationship = create_relationship(self.tenant, self.user,
                                                groups=create_default_tenant_groups())
        self.tenant_site = mommy.make('shared_schema_tenants.TenantSite',
                                      tenant=self.tenant)


class SharedSchemaTenantsAPITestCase(APITestCase):

    def setUp(self):
        self.tenant = mommy.make('shared_schema_tenants.Tenant')
        set_current_tenant(self.tenant.slug)
        self.user = User.objects.create_user(
            first_name='test', last_name='test',
            username='test', email='test@sharedschematenants.com',
            password='test')
        self.relationship = create_relationship(self.tenant, self.user,
                                                groups=create_default_tenant_groups())
        self.tenant_site = mommy.make('shared_schema_tenants.TenantSite',
                                      tenant=self.tenant)

