from django.db import models
import django.utils.version
from shared_schema_tenants.settings import DEFAULT_TENANT_SLUG
from shared_schema_tenants.managers import SingleTenantModelManager, MultipleTenantModelManager
from shared_schema_tenants.models import Tenant


def get_default_tenant():
    return Tenant.objects.filter(slug=DEFAULT_TENANT_SLUG).first()


class SingleTenantModelMixin(models.Model):
    tenant = models.ForeignKey('shared_schema_tenants.Tenant', default=get_default_tenant)

    if django.utils.version.get_complete_version()[1] < 10:
        objects = models.Manager()
    else:
        objects = SingleTenantModelManager()

    original_manager = models.Manager()
    tenant_objects = SingleTenantModelManager()

    class Meta:
        abstract = True
        if django.utils.version.get_complete_version()[1] >= 10:
            default_manager_name = 'original_manager'
            base_manager_name = 'original_manager'


class MultipleTenantsModelMixin(models.Model):
    tenants = models.ManyToManyField('shared_schema_tenants.Tenant')

    if django.utils.version.get_complete_version()[1] < 10:
        objects = models.Manager()
    else:
        objects = MultipleTenantModelManager()

    tenant_objects = MultipleTenantModelManager()
    original_manager = models.Manager()

    class Meta:
        abstract = True
        if django.utils.version.get_complete_version()[1] >= 10:
            default_manager_name = 'original_manager'
            base_manager_name = 'original_manager'
