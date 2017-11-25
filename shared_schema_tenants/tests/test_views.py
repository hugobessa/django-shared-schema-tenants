#!/usr/bin/env python
# -*- coding: utf-8 -*-

from rest_framework.test import APITestCase
from rest_framework import status
from django.contrib.auth.models import User
from model_mommy import mommy
from shared_schema_tenants.models import Tenant, TenantSite
from shared_schema_tenants.helpers.tenants import set_current_tenant, create_default_tenant_groups
from shared_schema_tenants.helpers.tenant_relationships import create_relationship


try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse


class TenantListViewTests(APITestCase):

    def setUp(self):
        self.tenants = mommy.make('shared_schema_tenants.Tenant', _quantity=10)
        set_current_tenant(self.tenants[0].slug)
        self.user = User.objects.create_user(
            first_name='test', last_name='test',
            username='test', email='test@sharedschematenants.com',
            password='test')
        groups = create_default_tenant_groups()
        create_relationship(self.tenants[0], self.user, groups)
        self.params = {
            'name': 'test 2',
            'slug': 'test-2',
            'extra_data': {
                "logo": "https://www.google.com.br/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png",
                "is_non_profit": True,
                "number_of_employees": 7,
            },
        }
        self.view_url = reverse('shared_schema_tenants:tenant_list')
        self.client.force_authenticate(self.user)

    def test_list(self):
        response = self.client.get(self.view_url, HTTP_TENANT_SLUG=self.tenants[0].slug)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create(self):
        response = self.client.post(self.view_url, self.params, HTTP_TENANT_SLUG=self.tenants[0].slug)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_invalid_extra_data(self):
        self.params['extra_data']['logo'] = 'test'
        response = self.client.post(self.view_url, self.params, HTTP_TENANT_SLUG=self.tenants[0].slug)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_empty_extra_data(self):
        self.params['extra_data'] = {}
        response = self.client.post(self.view_url, self.params, HTTP_TENANT_SLUG=self.tenants[0].slug)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class TenantDetailsViewTests(APITestCase):

    def setUp(self):
        self.tenants = mommy.make('shared_schema_tenants.Tenant', _quantity=10)
        set_current_tenant(self.tenants[0].slug)
        self.user = User.objects.create_user(
            first_name='test', last_name='test',
            username='test', email='test@sharedschematenants.com',
            password='test')
        groups = create_default_tenant_groups()
        create_relationship(self.tenants[0], self.user, groups)
        self.params = {
            'name': 'test 2',
            'slug': 'test-2',
            'extra_data': {
                "logo": "https://www.google.com.br/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png",
                "is_non_profit": True,
                "number_of_employees": 7,
            },
        }
        self.view_url = reverse('shared_schema_tenants:tenant_details')
        self.client.force_authenticate(self.user)

    def test_update(self):
        response = self.client.put(self.view_url, self.params, HTTP_TENANT_SLUG=self.tenants[0].slug)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tenant = Tenant.objects.get(slug=response.data['slug'])
        self.assertEqual(tenant.name, self.params['name'])
        self.assertEqual(tenant.slug, self.params['slug'])
        self.assertEqual(tenant.extra_data, self.params['extra_data'])

    def test_partial_update(self):
        response = self.client.patch(
            self.view_url, {"extra_data": {"number_of_employees": 10}},
            HTTP_TENANT_SLUG=self.tenants[0].slug)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        tenant = Tenant.objects.get(slug=self.tenants[0].slug)
        self.assertEqual(tenant.extra_data['number_of_employees'], 10)


class TenantSiteListViewTests(APITestCase):

    def setUp(self):
        self.tenant = mommy.make('shared_schema_tenants.Tenant')
        set_current_tenant(self.tenant.slug)
        self.user = User.objects.create_user(
            first_name='test', last_name='test',
            username='test', email='test@sharedschematenants.com',
            password='test')
        groups = create_default_tenant_groups()
        create_relationship(self.tenant, self.user, groups)

        self.tenant_site = mommy.make('shared_schema_tenants.TenantSite',
                                      tenant=self.tenant)

        self.params = {
            'domain': 'sharedschematenants.com'
        }
        self.view_url = reverse('shared_schema_tenants:tenant_site_list')
        self.client.force_authenticate(self.user)

    def test_list(self):
        response = self.client.get(self.view_url, HTTP_TENANT_SLUG=self.tenant.slug)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data), 1)
        self.assertTrue(response.data[0].get('id'), self.tenant_site.id)

    def test_create(self):
        response = self.client.post(self.view_url, self.params, HTTP_TENANT_SLUG=self.tenant.slug)
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['domain'], self.params['domain'])

        set_current_tenant(self.tenant.slug)
        tenant_site = TenantSite.objects.filter(id=response.data['id']).first()
        self.assertIsNotNone(tenant_site)


class TenantSiteDetailsViewTests(APITestCase):

    def setUp(self):
        self.tenant = mommy.make('shared_schema_tenants.Tenant')
        set_current_tenant(self.tenant.slug)
        self.user = User.objects.create_user(
            first_name='test', last_name='test',
            username='test', email='test@sharedschematenants.com',
            password='test')
        groups = create_default_tenant_groups()
        create_relationship(self.tenant, self.user, groups)

        self.tenant_site = mommy.make('shared_schema_tenants.TenantSite',
                                      tenant=self.tenant)

        self.params = {
            'domain': 'sharedschematenants.com'
        }
        self.view_url = reverse('shared_schema_tenants:tenant_site_details',
                                kwargs={'pk': self.tenant_site.pk})
        self.client.force_authenticate(self.user)

    def test_delete(self):
        response = self.client.delete(self.view_url, HTTP_TENANT_SLUG=self.tenant.slug)
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        tenant_site = TenantSite.objects.filter(pk=self.tenant_site.pk).first()
        self.assertIsNone(tenant_site)


class TenantSettingsDetailsViewTests(APITestCase):

    def setUp(self):
        self.tenant = mommy.make('shared_schema_tenants.Tenant')
        set_current_tenant(self.tenant.slug)
        self.user = User.objects.create_user(
            first_name='test', last_name='test',
            username='test', email='test@sharedschematenants.com',
            password='test')
        groups = create_default_tenant_groups()
        create_relationship(self.tenant, self.user, groups)

        self.params = {
            'notify_users_by_email': False
        }
        self.view_url = reverse('shared_schema_tenants:tenant_settings_details',
                                kwargs={'pk': self.tenant.pk})
        self.client.force_authenticate(self.user)

    def test_retrieve(self):
        response = self.client.get(self.view_url, HTTP_TENANT_SLUG=self.tenant.slug)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_update(self):
        response = self.client.post(self.view_url, self.params, HTTP_TENANT_SLUG=self.tenant.slug)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        self.tenant.refresh_from_db()
        self.assertEqual(
            self.tenant.settings['notify_users_by_email'],
            self.params['notify_users_by_email'])
