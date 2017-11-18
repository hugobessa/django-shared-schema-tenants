from django.conf import settings


def get_setting(settings_name):
    app_settings = getattr(settings, 'SHARED_SCHEMA_TENANTS_CUSTOM_DATA', {})
    settings_dict = {
        'CUSTOMIZABLE_MODELS': app_settings.get('CUSTOMIZABLE_MODELS', []),
        'CUSTOM_TABLES_FILTER_KEYWORD': app_settings.get('CUSTOM_TABLES_FILTER_KEYWORD', '_custom_tables'),
        'CUSTOM_TABLES_LABEL': app_settings.get('CUSTOM_TABLES_LABEL', '_custom_tables'),
        'CUSTOMIZABLE_MODELS_LIST_CREATE_PERMISSIONS': app_settings.get(
            'CUSTOMIZABLE_MODELS_LIST_CREATE_PERMISSIONS', ['shared_schema_tenants.permissions.IsTenantOwner']),
        'CUSTOMIZABLE_MODELS_RETRIEVE_UTPADE_DESTROY_PERMISSIONS': app_settings.get(
            'CUSTOMIZABLE_MODELS_RETRIEVE_UTPADE_DESTROY_PERMISSIONS',
            ['shared_schema_tenants.permissions.IsTenantOwner']),
        'CUSTOMIZABLE_TABLES_LABEL_SEPARATOR':
            app_settings.get('CUSTOMIZABLE_TABLES_LABEL_SEPARATOR', '__'),
    }

    return settings_dict.get(settings_name)
