from django.db.models import Manager
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from shared_schema_tenants.helpers.tenants import get_current_tenant
from shared_schema_tenants.exceptions import TenantNotFoundError


class SingleTenantModelManager(Manager):

    def get_queryset(self, tenant=None):
        if not tenant:
            tenant = get_current_tenant()
            if tenant:
                return super(SingleTenantModelManager, self).get_queryset().filter(tenant=tenant)
            else:
                raise TenantNotFoundError()
        else:
            return super(SingleTenantModelManager, self).get_queryset().filter(tenant=tenant)

    def create(self, tenant=None, *args, **kwargs):
        if not tenant:
            tenant = get_current_tenant()
            if tenant:
                kwargs['tenant'] = tenant
                return super(SingleTenantModelManager, self).create(*args, **kwargs)
            else:
                raise TenantNotFoundError()
        else:
            return super(SingleTenantModelManager, self).create(tenant=tenant, *args, **kwargs)


class MultipleTenantModelManager(Manager):

    def _original_get_queryset(self):
        return super(MultipleTenantModelManager, self).get_queryset()

    def get_queryset(self, tenant=None):
        if not tenant:
            tenant = get_current_tenant()
            if tenant:
                return super(MultipleTenantModelManager, self).get_queryset().filter(tenants=tenant)
            else:
                raise TenantNotFoundError()
        else:
            return super(MultipleTenantModelManager, self).get_queryset().filter(tenants=tenant)

    def create(self, tenant=None, *args, **kwargs):
        if not tenant:
            tenant = get_current_tenant()
            if tenant:
                with transaction.atomic():
                    try:
                        model_instance = self._original_get_queryset().get(**kwargs)
                    except ObjectDoesNotExist:
                        model_instance = super(MultipleTenantModelManager, self).create(*args, **kwargs)
                    model_instance.tenants.add(tenant)
                    return model_instance
            else:
                raise TenantNotFoundError()
        else:
            model_instance, created = super(
                MultipleTenantModelManager, self).create(*args, **kwargs)
            model_instance.tenants.add(tenant)
            return model_instance
