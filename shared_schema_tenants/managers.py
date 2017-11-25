from django.db.models import Manager
from shared_schema_tenants.helpers.tenants import get_current_tenant


class SingleTenantModelManager(Manager):

    def get_original_queryset(self, *args, **kwargs):
        return super(SingleTenantModelManager, self).get_queryset(*args, **kwargs)

    def get_queryset(self, tenant=None, *args, **kwargs):
        if not tenant:
            tenant = get_current_tenant()
            if tenant:
                return super(SingleTenantModelManager, self).get_queryset(*args, **kwargs).filter(tenant=tenant)
            else:
                return super(SingleTenantModelManager, self).get_queryset(*args, **kwargs).none()
        else:
            return super(SingleTenantModelManager, self).get_queryset(*args, **kwargs).filter(tenant=tenant)


class MultipleTenantModelManager(Manager):

    def get_original_queryset(self, *args, **kwargs):
        return super(MultipleTenantModelManager, self).get_queryset(*args, **kwargs)

    def get_queryset(self, tenant=None, *args, **kwargs):
        if not tenant:
            tenant = get_current_tenant()
            if tenant:
                return super(MultipleTenantModelManager, self).get_queryset(*args, **kwargs).filter(tenants=tenant)
            else:
                return super(MultipleTenantModelManager, self).get_queryset(*args, **kwargs).none()
        else:
            return super(MultipleTenantModelManager, self).get_queryset(*args, **kwargs).filter(tenants=tenant)
