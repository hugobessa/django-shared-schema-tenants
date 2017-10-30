from django.conf import settings


def get_setting(settings_name):
    app_settings = getattr(settings, 'SHARED_SCHEMA_TENANTS_CUSTOM_DATA', {})
    settings_dict = {
        'CUSTOMIZABLE_MODELS': getattr(app_settings, 'CUSTOMIZABLE_MODELS', [])
    }

    return settings_dict.get(settings_name)
