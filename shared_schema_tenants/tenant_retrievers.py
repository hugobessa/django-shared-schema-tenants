from django.contrib.sites.shortcuts import get_current_site
from django.contrib.sites.models import Site
from shared_schema_tenants.models import Tenant, TenantSite
from shared_schema_tenants.settings import get_setting
from shared_schema_tenants.exceptions import TenantNotFoundError


def retrieve_by_domain(request):
    try:
        return get_current_site(request).tenant_site.tenant
    except (TenantSite.DoesNotExist, Site.DoesNotExist):
        return None
    except Tenant.DoesNotExist:
        raise TenantNotFoundError()


def retrieve_by_http_header(request):
    try:
        tenant_http_header = 'HTTP_' + get_setting('TENANT_HTTP_HEADER').replace('-', '_').upper()
        return Tenant.objects.get(slug=request.META[tenant_http_header])
    except LookupError:
        return None
    except Tenant.DoesNotExist:
        raise TenantNotFoundError()


def retrieve_by_session(request):
    try:
        return Tenant.objects.get(slug=request.session['tenant_slug'])
    except (AttributeError, LookupError, Tenant.DoesNotExist):
        return None
    except Tenant.DoesNotExist:
        raise TenantNotFoundError()
