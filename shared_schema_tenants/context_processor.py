from shared_schema_tenants.helpers.tenants import get_current_tenant


def current_tenant(request):
    return {
        'tenant': get_current_tenant(),
    }
