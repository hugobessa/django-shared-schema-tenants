import platform
from django.utils.functional import SimpleLazyObject
from shared_schema_tenants.settings import get_setting
from shared_schema_tenants.models import Tenant
from shared_schema_tenants.utils import import_from_string


if platform.python_version_tuple()[0] == '2':
    import thread as threading
else:
    import threading


def get_tenant(request):
    if not hasattr(request, '_cached_tenant'):
        tenant_retrievers = get_setting('TENANT_RETRIEVERS')

        for tenant_retriever in tenant_retrievers:
            tenant = import_from_string(tenant_retriever)(request)
            if tenant:
                request._cached_tenant = tenant
                break

        if not getattr(request, '_cached_tenant', False):
            lazy_tenant = TenantMiddleware.get_current_tenant()
            if not lazy_tenant:
                return None

            lazy_tenant._setup()
            request._cached_tenant = lazy_tenant._wrapped

        elif get_setting('ADD_TENANT_TO_SESSION'):
            try:
                request.session['tenant_slug'] = request._cached_tenant.slug
            except AttributeError:
                pass

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


