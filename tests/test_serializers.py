from django.test import TestCase, override_settings, RequestFactory
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.conf import settings
from model_mommy import mommy
from shared_schema_tenants.serializers import (
    TenantSerializer, TenantSettingsSerializer, TenantSiteSerializer)
from shared_schema_tenants.models import Tenant, TenantSite, TenantRelationship
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
            }
        }

    def test_list(self):
        data = TenantSerializer(Tenant.objects.all(), many=True).data
        keys = ['name', 'slug', 'extra_data']
        self.assertEqual(len(data), Tenant.objects.all().count())
        try:
            self.assertCountEqual(data[0].keys(), keys)
        except AttributeError:
            self.assertEqual(len(data[0].keys()), len(keys))
            for key in keys:
                self.assertTrue(key in data[0].keys())


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
        self.assertDictEqual(serializer.errors, {'extra_data': {'logo': ['This field is required']}})

    def test_update(self):
        tenant = self.tenants[0]
        serializer = TenantSerializer(tenant, data=self.params)

        self.assertTrue(serializer.is_valid())
        serializer.save()

        tenant = Tenant.objects.get(slug=self.params['slug'])

        self.assertEqual(tenant.name, self.params['name'])
        self.assertEqual(tenant.slug, self.params['slug'])
        self.assertEqual(tenant.extra_data, self.params['extra_data'])
