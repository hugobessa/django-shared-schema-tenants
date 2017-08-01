from django.db import models
from model_tenants.settings import DEFAULT_TENANT_SLUG


def get_default_tenant():
    from model_tenants.models import Tenant
    return Tenant.objects.filter(slug=DEFAULT_TENANT_SLUG).first()


class SingleTenantModelMixin(models.Model):
    tenant = models.ForeignKey('model_tenants.Tenant', default=get_default_tenant)

    objects = SingleTenantModelManager()

    class Meta:
        abstract = True


class MultipleTenantsModelMixin(models.Model):
    tenants = models.ManyToManyField('model_tenants.Tenant')

    objects = MultipleTenantModelManager()

    class Meta:
        abstract = True
