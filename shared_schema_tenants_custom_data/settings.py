from django.conf import settings


def get_setting(settings_name):
    app_settings = getattr(settings, 'SHARED_SCHEMA_TENANTS_CUSTOM_DATA', {})
    settings_dict = {
        'CUSTOMIZABLE_MODELS': getattr(app_settings, 'CUSTOMIZABLE_MODELS', []),
        'CUSTOM_TABLES_FILTER_KEYWORD': getattr(app_settings, 'CUSTOM_TABLES_FILTER_KEYWORD', '_custom_tables'),
        'CUSTOM_TABLES_LABEL': getattr(app_settings, 'CUSTOM_TABLES_LABEL', '_custom_tables'),
        'CUSTOMIZABLE_TABLES_LABEL_SEPARATOR': getattr(
            app_settings, 'CUSTOMIZABLE_TABLES_LABEL_SEPARATOR', '__'),
    }

    return settings_dict.get(settings_name)
