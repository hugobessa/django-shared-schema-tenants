from collections import OrderedDict
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.text import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.fields import get_error_detail, set_value
from rest_framework.fields import SkipField
from shared_schema_tenants_custom_data.models import (
    TenantSpecificFieldDefinition, TenantSpecificFieldChunk, TenantSpecificTable,
    TenantSpecificTableRow)
from shared_schema_tenants.utils import import_item


def compose_list(funcs):
    def inner(data, funcs=funcs):
        return inner(funcs[-1](data), funcs[:-1]) if funcs else data
    return inner


class TenantSpecificFieldDefinitionCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = TenantSpecificFieldDefinition
        fields = ['id', 'name', 'data_type', 'is_required', 'default_value', 'validators']

    def create(self, validated_date):
        table_content_type = self.context['table_content_type']
        table_id = self.context.get('table_id')

        return TenantSpecificFieldDefinition.objects.create(
            table_content_type=table_content_type,
            table_id=table_id,
            **validated_date
        )


class TenantSpecificFieldDefinitionUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = TenantSpecificFieldDefinition
        fields = ['id', 'is_required', 'default_value', 'validators']

    def validate(self, data):
        if TenantSpecificFieldChunk.objects.filter(data['id']).exists():
            is_required = data.get('is_required', self.instance.is_required)
            default_value = data.get('default_value', self.instance.defaul_value)

            if is_required and not default_value:
                raise serializers.ValidationError(_(
                    'Your table already has data, so a new field must either be not required '
                    'or have a default value'))

        return data

    def update(self, instance, validated_date):
        instance.is_required = validated_date.get('is_required', instance.is_required)
        instance.default_value = validated_date.get('default_value', instance.default_value)
        instance.save()

        instance.validators.set(validated_date.get('validators', instance.validators))

        return instance


class TenantSpecificModelSerializer(serializers.ModelSerializer):

    serializer_tenant_specific_field_mapping = {
        'integer': serializers.IntegerField,
        'char': serializers.CharField,
        'text': serializers.TextField,
        'float': serializers.FloatField,
        'datetime': serializers.DateTimeField,
        'date': serializers.DateField,
    }

    def __init__(self, *args, **kwargs):
        ModelClass = self.Meta.model

        self.tenant_specific_fields_definitions = TenantSpecificFieldDefinition.objects.filter(
            table_content_type=ContentType.objects.get_from_model(ModelClass))

        for definition in self.tenant_specific_fields_definitions:
            field_kwargs = {}
            if definition.is_required:
                field_kwargs.update({
                    'required': True,
                    'allow_null': True
                })
            if definition.default_value is not None:
                field_kwargs.update({'default': definition.default_value})

            setattr(self, definition.name,
                    self.serializer_tenant_specific_field_mapping[definition.data_type](**field_kwargs))

        super(TenantSpecificModelSerializer, self).__init__(*args, **kwargs)

    def to_internal_value(self, data):
        ret = OrderedDict()
        errors = OrderedDict()

        for field in self.tenant_specific_fields_definitions:
            validators = []
            for validator_instance in field.validators.all():
                validator_function = import_item(validator_instance.module_path)
                validators.append(validator_function)

            validate_method = compose_list(validators)

            primitive_value = field.get_value(data)
            try:
                validated_value = field.run_validation(primitive_value)
                if validate_method is not None:
                    validated_value = validate_method(validated_value)
            except serializers.ValidationError as exc:
                errors[field.field_name] = exc.detail
            except DjangoValidationError as exc:
                errors[field.field_name] = get_error_detail(exc)
            except SkipField:
                pass
            else:
                set_value(ret, field.source_attrs, validated_value)

        if errors:
            raise serializers.ValidationError(errors)

        data.update(dict(ret))

        ret = super(TenantSpecificModelSerializer, self).to_internal_value(data)

        return ret


def get_tenant_specific_table_row_serializer_class(table_name):

    tenant_specific_fields_definitions = TenantSpecificFieldDefinition.objects.filter(
        table_content_type=ContentType.objects.get_from_model(TenantSpecificTable),
        table_id__in=TenantSpecificTable.objects.filter(name=table_name).values_list('id', flat=True)
    )

    class TenantSpecificTableRowSerializer(serializers.ModelSerializer):

        class Meta:
            model = TenantSpecificTableRow
            fields = ['id'] + tenant_specific_fields_definitions.values_list('name', flat=True)

        serializer_tenant_specific_field_mapping = {
            'integer': serializers.IntegerField,
            'char': serializers.CharField,
            'text': serializers.TextField,
            'float': serializers.FloatField,
            'datetime': serializers.DateTimeField,
            'date': serializers.DateField,
        }

        def __init__(self, *args, **kwargs):
            for definition in tenant_specific_fields_definitions:
                field_kwargs = {}
                if definition.is_required:
                    field_kwargs.update({
                        'required': True,
                        'allow_null': True
                    })
                if definition.default_value is not None:
                    field_kwargs.update({'default': definition.default_value})

                setattr(self, definition.name,
                        self.serializer_tenant_specific_field_mapping[definition.data_type](**field_kwargs))

            super(TenantSpecificModelSerializer, self).__init__(*args, **kwargs)

        def to_internal_value(self, data):
            ret = OrderedDict()
            errors = OrderedDict()

            for field in tenant_specific_fields_definitions:
                validators = []
                for validator_instance in field.validators.all():
                    validator_function = import_item(validator_instance.module_path)
                    validators.append(validator_function)

                validate_method = compose_list(validators)

                primitive_value = field.get_value(data)
                try:
                    validated_value = field.run_validation(primitive_value)
                    if validate_method is not None:
                        validated_value = validate_method(validated_value)
                except serializers.ValidationError as exc:
                    errors[field.field_name] = exc.detail
                except DjangoValidationError as exc:
                    errors[field.field_name] = get_error_detail(exc)
                except SkipField:
                    pass
                else:
                    set_value(ret, field.source_attrs, validated_value)

            if errors:
                raise serializers.ValidationError(errors)

            data.update(dict(ret))

            ret = super(TenantSpecificModelSerializer, self).to_internal_value(data)

            return ret

    return TenantSpecificTableRowSerializer
