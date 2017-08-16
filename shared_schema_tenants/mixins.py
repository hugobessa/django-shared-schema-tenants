from django.db import models
from shared_schema_tenants.settings import DEFAULT_TENANT_SLUG
from shared_schema_tenants.managers import SingleTenantModelManager, MultipleTenantModelManager
from shared_schema_tenants.models import Tenant


def get_default_tenant():
    return Tenant.objects.filter(slug=DEFAULT_TENANT_SLUG).first()


class SingleTenantModelMixin(models.Model):
    tenant = models.ForeignKey('shared_schema_tenants.Tenant', default=get_default_tenant)

    objects = SingleTenantModelManager()

    class Meta:
        abstract = True


class MultipleTenantsModelMixin(models.Model):
    tenants = models.ManyToManyField('shared_schema_tenants.Tenant')

    objects = MultipleTenantModelManager()

    class Meta:
        abstract = True
