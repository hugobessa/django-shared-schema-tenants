from model_tenants.settings import (
    DEFAULT_TENANT_SETTINGS_FIELDS)

from django.conf import settings

from model_tenants.helpers.tenant_json_field import TenantJsonFieldHelper


class TenantSettingsHelper(TenantJsonFieldHelper):
    TENANT_FIELDS = getattr(settings, 'TENANT_SETTINGS_FIELDS',
                            DEFAULT_TENANT_SETTINGS_FIELDS)

    def __init__(self, instance=None):
        super(TenantExtraDataHelper, self).__init__(
            instance_field_name='settings', instance=instance)
