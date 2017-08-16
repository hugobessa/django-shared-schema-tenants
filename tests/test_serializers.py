#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
test_serializers
------------

Tests for `django-shared-schema-tenants` serializers module.
"""

from django.test import TestCase, RequestFactory
from django.contrib.auth.models import User
from model_mommy import mommy
from shared_schema_tenants.serializers import (
    TenantSerializer, TenantSettingsSerializer, TenantSiteSerializer)
from shared_schema_tenants.models import Tenant, TenantSite
from shared_schema_tenants.middleware import TenantMiddleware


class TenantSerializerTests(TestCase):

    def setUp(self):
        self.tenants = mommy.make('shared_schema_tenants.Tenant', _quantity=10)
        self.user = User.objects.create_user(
            first_name='test', last_name='test',
            username='test', email='test@sharedschematenants.com',
            password='test')
        TenantMiddleware.set_tenant(self.tenants[0].slug)
        self.params = {
            'name': 'test 2',
            'slug': 'test-2',
            'extra_data': {
                "logo": "https://www.google.com.br/images/branding/googlelogo/1x/googlelogo_color_272x92dp.png",
                "is_non_profit": True,
                "number_of_employees": 7,
            },
        }

    def test_serialize(self):
        data = TenantSerializer(Tenant.objects.all().first()).data
        keys = ['name', 'slug', 'extra_data']
        try:
            self.assertCountEqual(data.keys(), keys)
        except AttributeError:
            self.assertEqual(len(data.keys()), len(keys))
            for key in keys:
                self.assertTrue(key in data.keys())

    def test_create(self):
        request = RequestFactory()
        request.user = self.user
        serializer = TenantSerializer(data=self.params, context={'request': request})
        self.assertTrue(serializer.is_valid())
        tenant = serializer.save()

        self.assertEqual(tenant.name, self.params['name'])
        self.assertEqual(tenant.slug, self.params['slug'])
        self.assertEqual(tenant.extra_data, self.params['extra_data'])

    def test_create_invalid_extra_data(self):
        request = RequestFactory()
        request.user = self.user

        self.params['extra_data']['logo'] = 'test'
        serializer = TenantSerializer(data=self.params, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertDictEqual(serializer.errors, {'extra_data': {'logo': ['This field must be a valid url']}})

    def test_create_empty_extra_data(self):
        request = RequestFactory()
        request.user = self.user

        self.params['extra_data'] = {}
        serializer = TenantSerializer(data=self.params, context={'request': request})
        self.assertFalse(serializer.is_valid())
        self.assertDictEqual(serializer.errors, {
            'extra_data': {
                'is_non_profit': ['This field is required'],
                'logo': ['This field is required'],
                'number_of_employees': ['This field is required'],
            }
        })

    def test_update(self):
        tenant = self.tenants[0]
        serializer = TenantSerializer(tenant, data=self.params)

        self.assertTrue(serializer.is_valid())
        serializer.save()

        tenant = Tenant.objects.get(slug=self.params['slug'])

        self.assertEqual(tenant.name, self.params['name'])
        self.assertEqual(tenant.slug, self.params['slug'])
        self.assertEqual(tenant.extra_data, self.params['extra_data'])

    def test_partial_update(self):
        tenant = self.tenants[0]
        serializer = TenantSerializer(tenant, data={"extra_data": {"number_of_employees": 10}}, partial=True)

        self.assertTrue(serializer.is_valid())
        serializer.save()

        tenant.refresh_from_db()

        self.assertEqual(tenant.extra_data['number_of_employees'], 10)


class TenantSiteSerializerTests(TestCase):

    def setUp(self):
        self.tenants = mommy.make('shared_schema_tenants.Tenant', _quantity=10)
        self.user = User.objects.create_user(
            first_name='test', last_name='test',
            username='test', email='test@sharedschematenants.com',
            password='test')

        self.params = {
            'domain': 'sharedschematenants.com'
        }
        TenantMiddleware.set_tenant(self.tenants[0].slug)

    def test_serialize(self):
        data = TenantSiteSerializer(TenantSite.objects.all().first()).data
        keys = ['id', 'domain']
        try:
            self.assertCountEqual(data.keys(), keys)
        except AttributeError:
            self.assertEqual(len(data.keys()), len(keys))
            for key in keys:
                self.assertTrue(key in data.keys())

    def test_create(self):
        serializer = TenantSiteSerializer(data=self.params)
        self.assertTrue(serializer.is_valid())
        tenant_site = serializer.save()
        self.assertEqual(tenant_site.site.domain, self.params['domain'])


class TenantSettingsSerializerTests(TestCase):

    def setUp(self):
        self.tenants = mommy.make('shared_schema_tenants.Tenant', _quantity=10)
        self.user = User.objects.create_user(
            first_name='test', last_name='test',
            username='test', email='test@sharedschematenants.com',
            password='test')

        self.params = {
            'notify_users_by_email': False
        }
        TenantMiddleware.set_tenant(self.tenants[0].slug)

    def test_serialize(self):
        data = TenantSettingsSerializer(Tenant.objects.all().first()).data
        keys = ['notify_users_by_email']
        try:
            self.assertCountEqual(data.keys(), keys)
        except AttributeError:
            self.assertEqual(len(data.keys()), len(keys))
            for key in keys:
                self.assertTrue(key in data.keys())

    def test_update(self):
        serializer = TenantSettingsSerializer(data=self.params)
        self.assertTrue(serializer.is_valid())
        tenant_site = serializer.save()
        self.assertEqual(
            tenant_site.settings['notify_users_by_email'],
            self.params['notify_users_by_email'])
