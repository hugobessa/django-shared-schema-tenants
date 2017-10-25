from django.db.models import Manager
from shared_schema_tenants_custom_data.querysets import TenantSpecificFieldsQueryset


class TenantSpecificFieldsModelManager(Manager):
    queryset = TenantSpecificFieldsQueryset
