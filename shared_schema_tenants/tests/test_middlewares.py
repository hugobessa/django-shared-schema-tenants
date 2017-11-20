import mock
from django.test import TestCase, RequestFactory
from django.http import HttpResponse
from shared_schema_tenants.middleware import TenantMiddleware, get_tenant
from shared_schema_tenants.helpers.tenants import create_tenant, set_current_tenant
from shared_schema_tenants.exceptions import TenantNotFoundError


try:
    from django.urls import reverse
except ImportError:
    from django.core.urlresolvers import reverse


class TenantMiddlewareTests(TestCase):

    @mock.patch('shared_schema_tenants.middleware.TenantMiddleware.process_request')
    @mock.patch('shared_schema_tenants.middleware.TenantMiddleware.process_response')
    def test_calls_process_request_and_process_response(self, process_request, process_response):
        factory = RequestFactory()
        request = factory.get(reverse('shared_schema_tenants:tenant_list'), HTTP_HOST='test.localhost:8000')

        response = HttpResponse()
        TenantMiddleware(lambda r: response).__call__(request)
        process_request.assert_called_once()
        process_response.assert_called_once()

    @mock.patch('shared_schema_tenants.middleware.get_tenant')
    def test_process_request_adds_tenant_to_request(self, get_tenant):
        tenant = create_tenant(name='test', slug='test', extra_data={}, domains=['test.localhost:8000'])
        get_tenant.return_value = tenant
        factory = RequestFactory()
        request = factory.get(reverse('shared_schema_tenants:tenant_list'), HTTP_HOST='test.localhost:8000')
        response = HttpResponse()
        request = TenantMiddleware(lambda r: response).process_request(request)

        self.assertEqual(request.tenant.slug, tenant.slug)
        get_tenant.assert_called_once()

    def test_call_returns_correct_response(self):
        tenant = create_tenant(name='test', slug='test', extra_data={}, domains=['test.localhost:8000'])
        get_tenant.return_value = tenant
        factory = RequestFactory()
        request = factory.get(reverse('shared_schema_tenants:tenant_list'), HTTP_HOST='test.localhost:8000')

        response = HttpResponse()
        processed_response = TenantMiddleware(lambda r: response).__call__(request)

        self.assertEqual(response, processed_response)


class GetTenantTests(TestCase):

    def test_with_correct_domain(self):
        tenant = create_tenant(name='test', slug='test', extra_data={}, domains=['test.localhost:8000'])
        factory = RequestFactory()
        request = factory.get(reverse('shared_schema_tenants:tenant_list'), HTTP_HOST='test.localhost:8000')
        retrieved_tenant = get_tenant(request)

        self.assertEqual(retrieved_tenant, tenant)

    def test_with_http_header(self):
        tenant = create_tenant(name='test', slug='test', extra_data={}, domains=['test.localhost:8000'])
        factory = RequestFactory()
        request = factory.get(reverse('shared_schema_tenants:tenant_list'), **{'HTTP_TENANT_SLUG': tenant.slug})

        retrieved_tenant = get_tenant(request)

        self.assertEqual(retrieved_tenant, tenant)

    def test_with_unexistent_tenant_in_http_header(self):
        create_tenant(name='test', slug='test', extra_data={}, domains=['test.localhost:8000'])
        factory = RequestFactory()
        request = factory.get(reverse('shared_schema_tenants:tenant_list'), **{'HTTP_TENANT_SLUG': 'unexistent'})

        with self.assertRaises(TenantNotFoundError):
            get_tenant(request)

    def test_with_previously_set_tenant(self):
        tenant = create_tenant(name='test', slug='test', extra_data={}, domains=['test.localhost:8000'])
        factory = RequestFactory()
        request = factory.get(reverse('shared_schema_tenants:tenant_list'))

        set_current_tenant(tenant.slug)
        retrieved_tenant = get_tenant(request)

        self.assertEqual(retrieved_tenant, tenant)

    def test_with_nothing(self):
        factory = RequestFactory()
        request = factory.get(reverse('shared_schema_tenants:tenant_list'))

        retrieved_tenant = get_tenant(request)

        self.assertEqual(retrieved_tenant, None)
