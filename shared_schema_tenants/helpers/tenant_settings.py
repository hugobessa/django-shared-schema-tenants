from shared_schema_tenants.settings import (
    DEFAULT_TENANT_SETTINGS_FIELDS, DEFAULT_TENANT_SETTINGS)

from shared_schema_tenants.helpers.tenant_json_field import TenantJSONFieldHelper


class TenantSettingsHelper(TenantJSONFieldHelper):
    TENANT_FIELDS = DEFAULT_TENANT_SETTINGS_FIELDS
    TENANT_DEFAULT_FIELDS_VALUES = DEFAULT_TENANT_SETTINGS

    def __init__(self, instance=None):
        super(TenantSettingsHelper, self).__init__(
            instance_field_name='settings', instance=instance)
