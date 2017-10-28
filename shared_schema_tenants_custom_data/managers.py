from django.db.models import Manager
from shared_schema_tenants_custom_data.querysets import TenantSpecificFieldsQueryset
from shared_schema_tenants.managers import SingleTenantModelManager


class TenantSpecificFieldsModelManager(Manager):
    queryset = TenantSpecificFieldsQueryset


class TenantSpecificTableRowManager(SingleTenantModelManager, TenantSpecificFieldsModelManager):
    pass
