from django.conf import settings

tenant_settings = getattr(settings, 'MODEL_TENANTS', {})


TENANT_SERIALIZER = (tenant_settings
                        .get('SERIALIZERS', {})
                        .get('TENANT_SERIALIZER', 
                             'model_tenants.serializers.TenantSerializer'))


TENANT_SITE_SERIALIZER = (tenant_settings
                            .get('SERIALIZERS', {})
                            .get('TENANT_SITE_SERIALIZER', 
                                'model_tenants.serializers.TenantSiteSerializer'))

TENANT_SETTINGS_SERIALIZER = (tenant_settings
                            .get('SERIALIZERS', {})
                            .get('TENANT_SETTINGS_SERIALIZER', 
                                'model_tenants.serializers.TenantSettingsSerializer'))

TENANT_RELATIONSHIP_SERIALIZER = (
    tenant_settings
        .get('SERIALIZERS', {})
        .get('TENANT_SITE_SERIALIZER', 
            'model_tenants.serializers.TenantSiteSerializer'))


DEFAULT_TENANT_SLUG = tenant_settings.get('DEFAULT_TENANT_SLUG', 'default')


DEFAULT_TENANT_SETTINGS_FIELDS = tenant_settings.get(
                                  'DEFAULT_TENANT_SETTINGS_FIELDS', {})


DEFAULT_TENANT_SETTINGS = tenant_settings.get(
                            'DEFAULT_TENANT_SETTINGS', {})


DEFAULT_TENANT_EXTRA_DATA_FIELDS = tenant_settings.get(
    'DEFAULT_TENANT_EXTRA_DATA_FIELDS', 
    {
        'logo': {
            'type': 'string',
            'default': None,
            'validators': [],
        }
    })


DEFAULT_SITE_DOMAIN = tenant_settings.get(
    'DEFAULT_SITE_DOMAIN',
    'localhost'
)