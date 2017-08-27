from shared_schema_tenants.settings import (
    DEFAULT_TENANT_EXTRA_DATA_FIELDS, DEFAULT_TENANT_EXTRA_DATA)

from shared_schema_tenants.helpers.tenant_json_field import TenantJSONFieldHelper


class TenantExtraDataHelper(TenantJSONFieldHelper):

    def __init__(self, instance=None):
        super(TenantExtraDataHelper, self).__init__(
            instance_field_name='extra_data', instance=instance,
            tenant_fields=DEFAULT_TENANT_EXTRA_DATA_FIELDS,
            tenant_default_fields_values=DEFAULT_TENANT_EXTRA_DATA)
