from django.db import models
from shared_schema_tenants.settings import get_setting
from shared_schema_tenants.managers import SingleTenantModelManager, MultipleTenantModelManager
from shared_schema_tenants.helpers.tenants import get_current_tenant
from shared_schema_tenants.exceptions import TenantNotFoundError


def get_default_tenant():
    from shared_schema_tenants.models import Tenant
    return Tenant.objects.filter(slug=get_setting('DEFAULT_TENANT_SLUG')).first()


class SingleTenantModelMixin(models.Model):
    tenant = models.ForeignKey(
        'shared_schema_tenants.Tenant', default=get_default_tenant)

    objects = SingleTenantModelManager()

    original_manager = models.Manager()
    tenant_objects = SingleTenantModelManager()

    class Meta:
        abstract = True
        default_manager_name = 'objects'
        base_manager_name = 'objects'

    def save(self, *args, **kwargs):
        if not hasattr(self, 'tenant'):
            self.tenant = get_current_tenant()

        if getattr(self, 'tenant', False):
            return super(SingleTenantModelMixin, self).save(*args, **kwargs)
        else:
            raise TenantNotFoundError()


class MultipleTenantsModelMixin(models.Model):
    tenants = models.ManyToManyField('shared_schema_tenants.Tenant')

    objects = MultipleTenantModelManager()

    tenant_objects = MultipleTenantModelManager()
    original_manager = models.Manager()

    class Meta:
        abstract = True
        default_manager_name = 'objects'
        base_manager_name = 'objects'

    def save(self, *args, **kwargs):
        tenant = get_current_tenant()

        if tenant:
            instance = super(MultipleTenantsModelMixin, self).save(*args, **kwargs)
            self.tenants.add(tenant)
            return instance
        else:
            raise TenantNotFoundError()
