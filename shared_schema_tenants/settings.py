from django.conf import settings

tenant_settings = getattr(settings, 'SHARED_SCHEMA_TENANTS', {})


TENANT_SERIALIZER = (tenant_settings
                     .get('SERIALIZERS', {})
                     .get('TENANT_SERIALIZER',
                          'shared_schema_tenants.serializers.TenantSerializer'))


TENANT_SITE_SERIALIZER = (tenant_settings
                          .get('SERIALIZERS', {})
                          .get('TENANT_SITE_SERIALIZER',
                               'shared_schema_tenants.serializers.TenantSiteSerializer'))

TENANT_SETTINGS_SERIALIZER = (tenant_settings
                              .get('SERIALIZERS', {})
                              .get('TENANT_SETTINGS_SERIALIZER',
                                   'shared_schema_tenants.serializers.TenantSettingsSerializer'))

TENANT_RELATIONSHIP_SERIALIZER = (
    tenant_settings
    .get('SERIALIZERS', {})
    .get('TENANT_SITE_SERIALIZER',
         'shared_schema_tenants.serializers.TenantSiteSerializer'))


DEFAULT_TENANT_SETTINGS_FIELDS = tenant_settings.get(
    'DEFAULT_TENANT_SETTINGS_FIELDS', {})


DEFAULT_TENANT_SETTINGS = {key: value.get('default')
                           for key, value
                           in DEFAULT_TENANT_SETTINGS_FIELDS.items()}


DEFAULT_TENANT_EXTRA_DATA_FIELDS = tenant_settings.get(
    'DEFAULT_TENANT_EXTRA_DATA_FIELDS',
    {})

DEFAULT_TENANT_EXTRA_DATA = {key: value.get('default')
                             for key, value
                             in DEFAULT_TENANT_EXTRA_DATA_FIELDS.items()}

DEFAULT_SITE_DOMAIN = tenant_settings.get(
    'DEFAULT_SITE_DOMAIN',
    'localhost'
)

TENANT_HTTP_HEADER = tenant_settings.get('TENANT_HTTP_HEADER', 'Tenant-Slug')
