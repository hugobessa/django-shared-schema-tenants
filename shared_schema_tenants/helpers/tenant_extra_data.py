from shared_schema_tenants.settings import (
    DEFAULT_TENANT_EXTRA_DATA_FIELDS, DEFAULT_TENANT_EXTRA_DATA)

from django.conf import settings

from shared_schema_tenants.helpers.tenant_json_field import TenantJSONFieldHelper


class TenantExtraDataHelper(TenantJSONFieldHelper):
    TENANT_FIELDS = DEFAULT_TENANT_EXTRA_DATA_FIELDS
    TENANT_DEFAULT_FIELDS_VALUES = DEFAULT_TENANT_EXTRA_DATA

    def __init__(self, instance=None):
        super(TenantExtraDataHelper, self).__init__(
            instance_field_name='extra_data', instance=instance)
