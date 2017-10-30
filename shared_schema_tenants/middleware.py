import platform
from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.models import Site
from django.utils.functional import SimpleLazyObject
from shared_schema_tenants.settings import get_setting
from shared_schema_tenants.models import Tenant, TenantSite

if platform.python_version_tuple()[0] == '2':
    import thread as threading
else:
    import threading


def get_tenant(request):
    if not hasattr(request, '_cached_tenant'):
        try:
            request._cached_tenant = get_current_site(request).tenant_site.tenant
            return request._cached_tenant
        except (TenantSite.DoesNotExist, Site.DoesNotExist):
            pass

        try:
            tenant_http_header = 'HTTP_' + get_setting('TENANT_HTTP_HEADER').replace('-', '_').upper()
            request._cached_tenant = Tenant.objects.get(slug=request.META[tenant_http_header])
        except LookupError:
            lazy_tenant = TenantMiddleware.get_current_tenant()
            if not lazy_tenant:
                return None

            lazy_tenant._setup()
            request._cached_tenant = lazy_tenant._wrapped
        except Tenant.DoesNotExist:
            return None

    return request._cached_tenant


class TenantMiddleware(object):
    _threadmap = {}

    def __init__(self, get_response):
        self.get_response = get_response
        # One-time configuration and initialization.

    @classmethod
    def get_current_tenant(cls):
        try:
            return cls._threadmap[threading.get_ident()]
        except KeyError:
            return None

    @classmethod
    def set_tenant(cls, tenant_slug):
        cls._threadmap[threading.get_ident()] = SimpleLazyObject(
            lambda: Tenant.objects.filter(slug=tenant_slug).first())

    @classmethod
    def clear_tenant(cls):
        del cls._threadmap[threading.get_ident()]

    def process_request(self, request):
        request.tenant = SimpleLazyObject(lambda: get_tenant(request))
        self._threadmap[threading.get_ident()] = request.tenant

        return request

    def process_exception(self, request, exception):
        try:
            del self._threadmap[threading.get_ident()]
        except KeyError:
            pass

    def process_response(self, request, response):
        try:
            del self._threadmap[threading.get_ident()]
        except KeyError:
            pass
        return response

    def __call__(self, request):
        # Code to be executed for each request before
        # the view (and later middleware) are called.
        request = self.process_request(request)
        response = self.get_response(request)
        return self.process_response(request, response)


