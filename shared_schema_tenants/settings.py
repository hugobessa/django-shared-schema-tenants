from django.conf import settings


def get_setting(settings_name):
    tenant_settings = getattr(settings, 'SHARED_SCHEMA_TENANTS', {})
    DEFAULT_TENANT_SETTINGS_FIELDS = tenant_settings.get(
        'DEFAULT_TENANT_SETTINGS_FIELDS', {})
    DEFAULT_TENANT_EXTRA_DATA_FIELDS = tenant_settings.get(
        'DEFAULT_TENANT_EXTRA_DATA_FIELDS', {})

    settings_dict = {
        "TENANT_SERIALIZER": (tenant_settings
                              .get('SERIALIZERS', {})
                              .get('TENANT_SERIALIZER',
                                   'shared_schema_tenants.serializers.TenantSerializer')),
        "TENANT_SITE_SERIALIZER": (tenant_settings
                                   .get('SERIALIZERS', {})
                                   .get('TENANT_SITE_SERIALIZER',
                                        'shared_schema_tenants.serializers.TenantSiteSerializer')),
        "TENANT_SETTINGS_SERIALIZER": (tenant_settings
                                       .get('SERIALIZERS', {})
                                       .get('TENANT_SETTINGS_SERIALIZER',
                                            'shared_schema_tenants.serializers.TenantSettingsSerializer')),
        "TENANT_RELATIONSHIP_SERIALIZER": (
            tenant_settings
            .get('SERIALIZERS', {})
            .get('TENANT_SITE_SERIALIZER',
                 'shared_schema_tenants.serializers.TenantSiteSerializer')),
        "DEFAULT_TENANT_SETTINGS_FIELDS": DEFAULT_TENANT_SETTINGS_FIELDS,
        "DEFAULT_TENANT_SETTINGS": {key: value.get('default')
                                    for key, value
                                    in DEFAULT_TENANT_SETTINGS_FIELDS.items()},
        "DEFAULT_TENANT_EXTRA_DATA_FIELDS": DEFAULT_TENANT_EXTRA_DATA_FIELDS,
        "DEFAULT_TENANT_EXTRA_DATA": {key: value.get('default')
                                      for key, value
                                      in DEFAULT_TENANT_EXTRA_DATA_FIELDS.items()},
        "DEFAULT_SITE_DOMAIN": tenant_settings.get(
            'DEFAULT_SITE_DOMAIN',
            'localhost'
        ),
        "DEFAULT_TENANT_SLUG": tenant_settings.get(
            'DEFAULT_TENANT_SLUG',
            'default'
        ),
        "TENANT_HTTP_HEADER": tenant_settings.get('TENANT_HTTP_HEADER', 'Tenant-Slug'),
        "DEFAULT_TENANT_OWNER_PERMISSIONS": tenant_settings.get(
            'DEFAULT_TENANT_OWNER_PERMISSIONS', [
                'shared_schema_tenants.add_tenant',
                'shared_schema_tenants.change_tenant',
                'shared_schema_tenants.delete_tenant',
                'shared_schema_tenants.add_tenantsite',
                'shared_schema_tenants.change_tenantsite',
                'shared_schema_tenants.delete_tenantsite',
                'shared_schema_tenants.add_tenantrelationship',
                'shared_schema_tenants.delete_tenantrelationship',
                'shared_schema_tenants.change_tenantrelationship',
            ])
    }

    return settings_dict.get(settings_name)
