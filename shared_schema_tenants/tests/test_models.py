#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_models
------------

Tests for `django-shared-schema-tenants` models module.
"""

from django.test import TestCase
from django.contrib.sites.models import Site
from django.contrib.auth.models import User
from shared_schema_tenants.models import Tenant, TenantSite, TenantRelationship
from shared_schema_tenants.middleware import TenantMiddleware


class TenantTests(TestCase):

    def test_create(self):
        tenant = Tenant(name='test', slug='test')
        tenant.save()
        TenantMiddleware.set_tenant(tenant)
        self.assertEqual(Tenant.objects.all().count(), 1)
        self.assertEqual(tenant.tenant_sites.all().count(), 0)


class TenantSiteTests(TestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(name='test', slug='test')
        self.site = Site.objects.create(name='test', domain="test.site.com")
        TenantMiddleware.set_tenant(self.tenant)

    def test_create(self):
        TenantSite.objects.create(tenant=self.tenant, site=self.site)
        self.assertEqual(TenantSite.objects.all().count(), 1)


class TenantRelationshipTests(TestCase):

    def setUp(self):
        self.tenant = Tenant.objects.create(name='test', slug='test')
        self.user = User.objects.create_user(
            first_name='test', last_name='test',
            username='test', email='test@sharedschematenants.com',
            password='test')
        TenantMiddleware.set_tenant(self.tenant)

    def test_create(self):
        TenantRelationship.objects.create(tenant=self.tenant, user=self.user)
        self.assertEqual(TenantRelationship.objects.all().count(), 1)
