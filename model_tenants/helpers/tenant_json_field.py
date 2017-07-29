from model_tenants.exceptions import TenantFieldTypeConfigurationError
from model_tenants.middleware import TenantMiddleware

class TenantJsonFieldHelper:
    TYPES_TO_INTERNAL_MAP = {
        'string': [str],
        'number': [int, float],
        'boolean': [bool],
        'list': [list],
        'object': [dict],
    }

    TENANT_FIELDS = {}
    TENANT_DEFAULT_FIELDS_VALUES = {}

    def __init__(self, instance_field_name, instance=None):
        if instance == None:
            instance = TenantMiddleware.get_current_tenant()

        self.instance = instance
        self.instance_field_name = instance_field_name

    def get_tenant_fields(self):
        return getattr(self, 'TENANT_FIELDS', {})

    def get_tenant_default_fields_values(self):
        return getattr(self, 'TENANT_DEFAULT_FIELDS_VALUES', {})

    def get_tenant(self):
        self.instance.refresh_with_db()
        return self.instance

    def get_field(self, instance, field_key):
        fields = getattr(instance, self.field_name, {})
        return fields.get(field_key, None)

    def validate_field(self, context, key, value, original_value=None):
        tenant_fields = get_tenant_fields()

        try:
            field = tenant_fields[key]
        except KeyError:
            raise ValidationError(_('%(field)s is not a valid field') % key)

        try:
            field_type = field['type']
        except KeyError:
            raise TenantFieldTypeConfigurationError((
                'You must define a valid type for tenant setting '
                'field "%(field)s" in "TENANT_SETTINGS_FIELDS"') % key)

        if field_type not in self.TYPES_TO_INTERNAL_MAP.keys():
            raise TenantFieldTypeConfigurationError((
                '"%(wrong_type)s" of field %(field)s is not a valid type. '
                'Use one of these: %(valid_types)s') % {
                    'wrong_type': field_type,
                    'field': key,
                    'valid_types': ', '.join(
                        [('"%s"' % t) for t in self.TYPES_TO_INTERNAL_MAP.keys()])
            })

        if type(value) not in self.TYPES_TO_INTERNAL_MAP[field_type]:
            raise ValidationError({
                'key': [
                    _('%(field)s must be a valid %(field_type)s') % key, field_type
                ]
            })

        for validator in field.get('validators', []):
            value = validator(context, value, original_value)

        return value

    def validate_fields(self,context, data):
        fields = getattr(self.instance, self.field, {})

        for key, value in data.items():
            data[key] = validate_field(
                context, key, value, get_setting(tenant, key))

        return data

    def update_fields(self, validated_data, partial=False, commit=True):
        if not partial:
            setattr(
                self.instance.settings,
                self.instance_field_name,
                dict(
                    self.get_tenant_default_fields_values(),
                    **validated_data
                )
            )
        else:
            setattr(
                self.instance.settings,
                self.instance_field_name,
                dict(tenant.settings, **validated_data)
            )

        if commit:
            self.instance.save()

        return self.instance

    def update_field(self, key, value, commit=True):
        return update_fields({key: value}, partial=True, commit=True)
