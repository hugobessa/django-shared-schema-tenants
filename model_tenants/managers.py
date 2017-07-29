from django.db.models import Manager

class SingleTenantModelManager(Manager):

    def get_queryset(self):
        from model_tenants.middleware import TenantMiddleware
        tenant = TenantMiddleware.get_current_tenant()
        if tenant:
            return super().get_queryset().filter(tenant=tenant)
        else:
            raise TenantNotFoundError()

    def create(self, *args, **kwargs):
        from model_tenants.middleware import TenantMiddleware
        tenant = TenantMiddleware.get_current_tenant()
        if tenant:
            return super().get_queryset().filter(tenant=tenant)
        else:
            raise TenantNotFoundError()

class MultipleTenantModelManager(Manager):

    def get_queryset(self):
        from model_tenants.middleware import TenantMiddleware
        tenant = TenantMiddleware.get_current_tenant()
        if tenant:
            return super().get_queryset().filter(tenants=tenant)
        else:
            raise TenantNotFoundError()

    def create(self, *args, **kwargs):
        from model_tenants.middleware import TenantMiddleware
        tenant = TenantMiddleware.get_current_tenant()
        if tenant:
            return super().get_queryset().filter(tenants=tenant)
        else:
            raise TenantNotFoundError()
