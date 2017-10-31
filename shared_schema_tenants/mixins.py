from django.db import models
from shared_schema_tenants.settings import get_setting
from shared_schema_tenants.managers import SingleTenantModelManager, MultipleTenantModelManager
from shared_schema_tenants.models import Tenant


def get_default_tenant():
    return Tenant.objects.filter(slug=get_setting('DEFAULT_TENANT_SLUG')).first()


class SingleTenantModelMixin(models.Model):
    tenant = models.ForeignKey('shared_schema_tenants.Tenant', default=get_default_tenant)

    objects = SingleTenantModelManager()

    original_manager = models.Manager()
    tenant_objects = SingleTenantModelManager()

    class Meta:
        abstract = True
        default_manager_name = 'original_manager'
        base_manager_name = 'original_manager'


class MultipleTenantsModelMixin(models.Model):
    tenants = models.ManyToManyField('shared_schema_tenants.Tenant')

    objects = MultipleTenantModelManager()

    tenant_objects = MultipleTenantModelManager()
    original_manager = models.Manager()

    class Meta:
        abstract = True
        default_manager_name = 'original_manager'
        base_manager_name = 'original_manager'
