from django.db.models import Manager
from django.db import transaction
from shared_schema_tenants.helpers.tenants import get_current_tenant
from shared_schema_tenants.exceptions import TenantNotFoundError


class SingleTenantModelManager(Manager):

    def get_queryset(self, tenant=None):
        if not tenant:
            tenant = get_current_tenant()
            if tenant:
                return super().get_queryset().filter(tenant=tenant)
            else:
                raise TenantNotFoundError()
        else:
            return super().get_queryset().filter(tenant=tenant)

    def create(self, tenant=None, *args, **kwargs):
        if not tenant:
            tenant = get_current_tenant()
            if tenant:
                kwargs['tenant'] = tenant
                return super().create(*args, **kwargs)
            else:
                raise TenantNotFoundError()
        else:
            return super().create(tenant=tenant, *args, **kwargs)


class MultipleTenantModelManager(Manager):

    def get_queryset(self, tenant=None):
        if not tenant:
            tenant = get_current_tenant()
            if tenant:
                return super().get_queryset().filter(tenants=tenant)
            else:
                raise TenantNotFoundError()
        else:
            return super().get_queryset().filter(tenants=tenant)

    def create(self, tenant=None, *args, **kwargs):
        if not tenant:
            tenant = get_current_tenant()
            if tenant:
                with transaction.atomic():
                    model_instance = super().create(*args, **kwargs)
                    model_instance.tenants.add(tenant)
            else:
                raise TenantNotFoundError()
        else:
            return super().create(tenants=tenant)
