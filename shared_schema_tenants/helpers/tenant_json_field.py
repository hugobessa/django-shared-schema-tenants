import sys
from django.core.exceptions import ValidationError
from django.utils.text import ugettext_lazy as _
from shared_schema_tenants.exceptions import TenantFieldTypeConfigurationError
from shared_schema_tenants.helpers.tenants import get_current_tenant


class TenantJSONFieldHelper(object):
    TYPES_TO_INTERNAL_MAP = {
        'string': [str],
        'number': [int, float],
        'boolean': [bool],
        'list': [list],
        'object': [dict],
    }

    def __init__(self, instance_field_name, instance=None,
                 tenant_fields={}, tenant_default_fields_values={}):
        if not instance:
            instance = get_current_tenant()

        self.instance = instance
        self.instance_field_name = instance_field_name
        self.tenant = get_current_tenant()
        self.tenant_fields = tenant_fields
        self.tenant_default_fields_values = tenant_default_fields_values

        if sys.version_info < (3, 4):
            self.TYPES_TO_INTERNAL_MAP['string'].append(type(u''))

    def get_tenant_fields(self):
        return getattr(self, 'tenant_fields', {})

    def get_tenant_default_fields_values(self):
        return getattr(self, 'tenant_default_fields_values', {})

    def get_tenant(self):
        return self.instance

    def get_field(self, instance, field_key):
        fields = getattr(instance, self.instance_field_name)
        if fields:
            return fields.get(field_key, None)

        return None

    def validate_field(self, context, key, value, original_value=None):
        tenant_fields = self.get_tenant_fields()

        try:
            field = tenant_fields[key]
        except KeyError:
            raise ValidationError(_('%(field)s is not a valid field') % {'field': key})

        try:
            field_type = field['type']
        except KeyError:
            raise TenantFieldTypeConfigurationError((
                'You must define a valid type for tenant setting '
                'field "%(field)s" in "TENANT_SETTINGS_FIELDS"') % {'field': key})

        if field_type not in self.TYPES_TO_INTERNAL_MAP.keys():
            raise TenantFieldTypeConfigurationError((
                '"%(wrong_type)s" of field %(field)s is not a valid type. '
                'Use one of these: %(valid_types)s') % {
                    'wrong_type': field_type,
                    'field': key,
                    'valid_types': ', '.join(
                        [('"%s"' % t) for t in self.TYPES_TO_INTERNAL_MAP.keys()])
            })

        if tenant_fields[key].get('required', True):
            if value == None or value == '':  # noqa
                raise ValidationError({
                    key: [
                        _('This field is required')
                    ]
                })
            if type(value) not in self.TYPES_TO_INTERNAL_MAP[field_type]:
                raise ValidationError({
                    key: [
                        _('%(field)s must be a valid %(field_type)s') % {
                            'field': key, 'field_type': field_type}
                    ]
                })

        for validator in field.get('validators', []):
            try:
                value = validator(context, value, original_value)
            except ValidationError as e:
                raise ValidationError({key: [e]})
        return value

    def validate_fields(self, context, data, partial=False):
        errors = {}
        has_errors = False
        for key in self.get_tenant_fields().keys():
            value = data.get(key)
            if not value and partial:
                continue

            try:
                data[key] = self.validate_field(
                    context, key, value, self.get_field(self.tenant, key))
            except ValidationError as e:
                has_errors = True
                errors = dict(errors, **e.message_dict)

        if has_errors:
            raise ValidationError(errors)

        return data

    def update_fields(self, validated_data, partial=False, commit=True):
        if not partial:
            setattr(
                self.instance,
                self.instance_field_name,
                validated_data
            )
        else:
            setattr(
                self.instance,
                self.instance_field_name,
                dict(self.tenant.settings, **validated_data)
            )

        if commit:
            self.instance.save()

        return self.instance

    def update_field(self, key, value, commit=True):
        return self.update_fields({key: value}, partial=True, commit=commit)
