from collections import OrderedDict
from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError as DjangoValidationError
from django.utils.text import ugettext_lazy as _
from rest_framework import serializers
from rest_framework.fields import get_error_detail, set_value
from rest_framework.fields import SkipField
from shared_schema_tenants.utils import import_item
from shared_schema_tenants_custom_data.settings import get_setting
from shared_schema_tenants_custom_data.models import (
    TenantSpecificFieldDefinition, TenantSpecificTable, TenantSpecificTableRow)
from shared_schema_tenants_custom_data.utils import compose_list
from shared_schema_tenants_custom_data.helpers.custom_tables_helpers import get_custom_table_manager


class TenantSpecificFieldDefinitionCreateSerializer(serializers.ModelSerializer):

    class Meta:
        model = TenantSpecificFieldDefinition
        fields = ['id', 'name', 'data_type', 'is_required', 'default_value', 'validators']

    def create(self, validated_date):
        table_content_type = getattr(self, 'table_content_type', None)
        table_id = getattr(self, 'table_id', None)

        validators = validated_date.pop('validators', [])
        definition = TenantSpecificFieldDefinition.objects.create(
            table_content_type=table_content_type,
            table_id=table_id,
            **validated_date
        )

        for v in validators:
            definition.validators.add(v)

        return definition


class TenantSpecificFieldDefinitionUpdateSerializer(serializers.ModelSerializer):

    class Meta:
        model = TenantSpecificFieldDefinition
        fields = ['id', 'is_required', 'default_value', 'validators']

    def validate(self, data):
        if hasattr(self, 'instance') and getattr(self, 'instance', False):
            is_required = data.get('is_required', self.instance.is_required)
            default_value = data.get('default_value', self.instance.default_value)

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


class TenantSpecificFieldsModelDefinitionsUpdateSerializer(serializers.ModelSerializer):

    fields_definitions = serializers.JSONField()

    class Meta:
        model = ContentType
        fields = ['fields_definitions']

    def to_representation(self, obj):
        return {
            'name': '%s%s%s' % (
                get_setting('CUSTOM_TABLES_LABEL'),
                get_setting('CUSTOMIZABLE_TABLES_LABEL_SEPARATOR'),
                obj.name
            ),
            'fields_definitions': TenantSpecificFieldDefinitionCreateSerializer(
                TenantSpecificFieldDefinition.objects.filter(table_content_type=obj),
                many=True
            ).data,
        }

    def validate_fields_definitions(self, definitions):
        definitions_errors = []
        definitions_serializers = []
        definitions_have_errors = False
        new_definitions_ids = [y['id'] for y in definitions if y.get('id', False)]
        for definition_dict in definitions:
            if definition_dict.get('id', False):
                definition_serializer = TenantSpecificFieldDefinitionUpdateSerializer(
                    TenantSpecificFieldDefinition.objects.get(id=definition_dict.get('id')),
                    data=definition_dict, context=self.context)
            else:
                definition_serializer = TenantSpecificFieldDefinitionCreateSerializer(
                    data=definition_dict, context=self.context)

            if definition_serializer.is_valid():
                definitions_errors.append({})
                definitions_serializers.append(definition_serializer)
            else:
                definitions_errors.append(definition_serializer.errors)
                definitions_have_errors = True

        if definitions_have_errors:
            raise serializers.ValidationError(definitions_errors)

        return {
            'serializers': definitions_serializers,
            'deleted': TenantSpecificFieldDefinition.objects.filter(
                table_content_type=self.instance).exclude(id__in=new_definitions_ids)
        }

    def update(self, instance, validated_data):
        if self.validated_data.get('fields_definitions', False):
            self.validated_data['fields_definitions']['deleted'].delete()
            for definitions_serializer in self.validated_data['fields_definitions']['serializers']:
                definitions_serializer.table_content_type = instance
                definitions_serializer.save()

        return instance


class TenantSpecificTableSerializer(serializers.ModelSerializer):

    fields_definitions = serializers.JSONField()

    class Meta:
        model = TenantSpecificTable
        fields = ['name', 'fields_definitions']

    def to_representation(self, obj):
        return {
            'name': '%s%s%s' % (
                get_setting('CUSTOM_TABLES_LABEL'),
                get_setting('CUSTOMIZABLE_TABLES_LABEL_SEPARATOR'),
                obj.name
            ),
            'fields_definitions': TenantSpecificFieldDefinitionCreateSerializer(
                obj.fields_definitions, many=True).data,
        }

    def validate_name(self, name):
        table_slug_parts = name.split(get_setting('CUSTOMIZABLE_TABLES_LABEL_SEPARATOR'))
        app = table_slug_parts[0]

        if app != get_setting('CUSTOM_TABLES_LABEL') or len(table_slug_parts) < 2:
            raise serializers.ValidationError(_("This is not a valid custom table name"))

        return table_slug_parts[-1]

    def validate_fields_definitions(self, definitions):
        definitions_errors = []
        definitions_serializers = []
        definitions_have_errors = False
        new_definitions_ids = [y['id'] for y in definitions if y.get('id', False)]
        for definition_dict in definitions:
            if definition_dict.get('id', False):
                definition_serializer = TenantSpecificFieldDefinitionUpdateSerializer(
                    TenantSpecificFieldDefinition.objects.get(id=definition_dict.get('id')),
                    data=definition_dict, context=self.context)
            else:
                definition_serializer = TenantSpecificFieldDefinitionCreateSerializer(
                    data=definition_dict, context=self.context)

            if definition_serializer.is_valid():
                definitions_errors.append({})
                definitions_serializers.append(definition_serializer)
            else:
                definitions_errors.append(definition_serializer.errors)
                definitions_have_errors = True

        if definitions_have_errors:
            raise serializers.ValidationError(definitions_errors)

        return {
            'serializers': definitions_serializers,
            'deleted': self.instance.fields_definitions.exclude(id__in=new_definitions_ids) if self.instance else None
        }

    def create(self, validated_data):
        table_name = validated_data.get('name')
        table = TenantSpecificTable.objects.create(name=table_name)

        if self.validated_data.get('fields_definitions', False):
            for definitions_serializer in self.validated_data['fields_definitions']['serializers']:
                definitions_serializer.table_id = table.id
                definitions_serializer.table_content_type = ContentType.objects.get_for_model(TenantSpecificTable)
                definitions_serializer.save()

        return table

    def update(self, instance, validated_data):
        if validated_data.get('name', False):
            table_name = validated_data.get('name')
            instance.name = table_name
            instance.save()

        if self.validated_data.get('fields_definitions', False):
            self.validated_data['fields_definitions']['deleted'].delete()
            table_content_type = ContentType.objects.get_for_model(TenantSpecificTable)
            for definitions_serializer in self.validated_data['fields_definitions']['serializers']:
                definitions_serializer.table_id = instance.id
                definitions_serializer.table_content_type = table_content_type
                definitions_serializer.save()

        return instance


class TenantSpecificModelSerializer(serializers.ModelSerializer):

    serializer_tenant_specific_field_mapping = {
        'integer': serializers.IntegerField,
        'char': serializers.CharField,
        'text': serializers.CharField,
        'float': serializers.FloatField,
        'datetime': serializers.DateTimeField,
        'date': serializers.DateField,
    }

    data_type_fields = {
        'integer': models.IntegerField(),
        'char': models.CharField(max_length=255),
        'text': models.TextField(),
        'float': models.FloatField(),
        'datetime': models.DateTimeField(),
        'date': models.DateField(),
    }

    def __init__(self, *args, **kwargs):
        ModelClass = self.Meta.model

        self.tenant_specific_fields_definitions = TenantSpecificFieldDefinition.objects.filter(
            table_content_type=ContentType.objects.get_for_model(ModelClass))

        self.tenant_specific_fields_names = list(
            self.tenant_specific_fields_definitions.values_list('name', flat=True))

        for definition in self.tenant_specific_fields_definitions:
            if not hasattr(self, definition.name):
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

    def get_field_names(self, declared_fields, info):
        fields = super(TenantSpecificModelSerializer, self).get_field_names(declared_fields, info)
        return fields + self.tenant_specific_fields_names

    def to_internal_value(self, data):
        ret = OrderedDict()
        errors = OrderedDict()

        for field in self.tenant_specific_fields_definitions:
            validators = []
            for validator_instance in field.validators.all():
                validator_function = import_item(validator_instance.module_path)
                validators.append(validator_function)

            validate_method = compose_list(validators)

            primitive_value = self.fields.get(field.name).get_value(data)
            try:
                validated_value = self.fields.get(field.name).run_validation(primitive_value)
                if validate_method is not None:
                    validated_value = validate_method(validated_value)
            except serializers.ValidationError as exc:
                errors[field.name] = exc.detail
            except DjangoValidationError as exc:
                errors[field.name] = get_error_detail(exc)
            except SkipField:
                pass
            else:
                set_value(ret, self.fields.get(field.name).source_attrs, validated_value)

        if errors:
            raise serializers.ValidationError(errors)

        data.update(dict(ret))

        ret = super(TenantSpecificModelSerializer, self).to_internal_value(data)

        return ret

    def build_field(self, field_name, info, model_class, nested_depth):
        tenat_specific_fields_names = list(
            self.tenant_specific_fields_definitions.values_list('name', flat=True))
        if field_name in tenat_specific_fields_names:
            definition = self.tenant_specific_fields_definitions.get(name=field_name)
            return self.build_standard_field(field_name, self.data_type_fields[definition.data_type])

        return super(TenantSpecificModelSerializer, self).build_field(
            field_name, info, model_class, nested_depth)

    def create(self, validated_data):
        ModelClass = self.Meta.model
        instance = ModelClass.objects.create(**validated_data)
        return ModelClass.objects.get(pk=instance.pk)

    def update(self, instance, validated_data):
        ModelClass = self.Meta.model
        instance = super(TenantSpecificModelSerializer, self).update(instance, validated_data)
        return ModelClass.objects.get(pk=instance.pk)


def get_tenant_specific_table_row_serializer_class(table_name):

    tenant_specific_fields_definitions = TenantSpecificFieldDefinition.objects.filter(
        table_content_type=ContentType.objects.get_for_model(TenantSpecificTable),
        table_id__in=TenantSpecificTable.objects.filter(name=table_name).values_list('id', flat=True)
    )

    class TenantSpecificTableRowSerializer(serializers.ModelSerializer):

        class Meta:
            model = TenantSpecificTableRow
            fields = ['id'] + list(tenant_specific_fields_definitions.values_list('name', flat=True))

        serializer_tenant_specific_field_mapping = {
            'integer': serializers.IntegerField,
            'char': serializers.CharField,
            'text': serializers.CharField,
            'float': serializers.FloatField,
            'datetime': serializers.DateTimeField,
            'date': serializers.DateField,
        }

        data_type_fields = {
            'integer': models.IntegerField(),
            'char': models.CharField(max_length=255),
            'text': models.TextField(),
            'float': models.FloatField(),
            'datetime': models.DateTimeField(),
            'date': models.DateField(),
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

            super(TenantSpecificTableRowSerializer, self).__init__(*args, **kwargs)

        def to_internal_value(self, data):
            ret = OrderedDict()
            errors = OrderedDict()

            for field in tenant_specific_fields_definitions:
                validators = []
                for validator_instance in field.validators.all():
                    validator_function = import_item(validator_instance.module_path)
                    validators.append(validator_function)

                validate_method = compose_list(validators)

                primitive_value = self.fields.get(field.name).get_value(data)
                try:
                    validated_value = self.fields.get(field.name).run_validation(primitive_value)
                    if validate_method is not None:
                        validated_value = validate_method(validated_value)
                except serializers.ValidationError as exc:
                    errors[field.name] = exc.detail
                except DjangoValidationError as exc:
                    errors[field.name] = get_error_detail(exc)
                except SkipField:
                    pass
                else:
                    set_value(ret, self.fields.get(field.name).source_attrs, validated_value)

            if errors:
                raise serializers.ValidationError(errors)

            data.update(dict(ret))

            ret = super(TenantSpecificTableRowSerializer, self).to_internal_value(data)

            return ret

        def build_field(self, field_name, info, model_class, nested_depth):
            if field_name in list(tenant_specific_fields_definitions.values_list('name', flat=True)):
                definition = tenant_specific_fields_definitions.get(name=field_name)
                return self.build_standard_field(field_name, self.data_type_fields[definition.data_type])

            return super(TenantSpecificTableRowSerializer, self).build_field(
                field_name, info, model_class, nested_depth)

        def create(self, validated_data):
            instance = get_custom_table_manager(table_name).create(**validated_data)
            return get_custom_table_manager(table_name).get(pk=instance.pk)

        def update(self, instance, validated_data):
            instance = super(TenantSpecificTableRowSerializer, self).update(instance, validated_data)
            return get_custom_table_manager(table_name).get(pk=instance.pk)

    return TenantSpecificTableRowSerializer
