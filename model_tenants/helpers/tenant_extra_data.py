from model_tenants.constants import (
    DEFAULT_TENANT_EXTRA_DATA_FIELDS)

from django.conf import settings

from model_tenants.helpers.tenant_json_field import TenantJsonFieldHelper


class TenantExtraDataHelper(TenantJsonFieldHelper):
    TENANT_FIELDS = getattr(settings, 'TENANT_EXTRA_DATA_FIELDS',
                            DEFAULT_TENANT_EXTRA_DATA_FIELDS)

    def __init__(self, instance=None):
        super(TenantExtraDataHelper, self).__init__(
            instance_field_name='extra_data', instance=instance)
