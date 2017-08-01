from django.db.models import Manager
from model_tenants.helpers.tenants import get_current_tenant


class SingleTenantModelManager(Manager):

    def get_queryset(self):
        tenant = get_current_tenant()
        if tenant:
            return super().get_queryset().filter(tenant=tenant)
        else:
            raise TenantNotFoundError()

    def create(self, *args, **kwargs):
        tenant = get_current_tenant()
        if tenant:
            return super().get_queryset().filter(tenant=tenant)
        else:
            raise TenantNotFoundError()


class MultipleTenantModelManager(Manager):

    def get_queryset(self):
        tenant = get_current_tenant()
        if tenant:
            return super().get_queryset().filter(tenants=tenant)
        else:
            raise TenantNotFoundError()

    def create(self, *args, **kwargs):
        tenant = get_current_tenant()
        if tenant:
            return super().get_queryset().filter(tenants=tenant)
        else:
            raise TenantNotFoundError()
