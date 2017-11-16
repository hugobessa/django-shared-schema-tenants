from django.db import models
from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey

from shared_schema_tenants.helpers.tenants import get_current_tenant
from shared_schema_tenants_custom_data.managers import TenantSpecificFieldsModelManager
from shared_schema_tenants_custom_data.helpers.custom_tables_helpers import (
    _get_pivot_table_class_for_data_type)


class TenantSpecificFieldsModelMixin(models.Model):
    objects = TenantSpecificFieldsModelManager()

    def __init__(self, *args, **kwargs):
        table_id = kwargs.get('table_id', getattr(kwargs.get('table'), 'id', None))
        definitions = self.get_definitions(table_id=table_id)
        for definition in definitions:
            if definition.name in kwargs.keys():
                setattr(self, definition.name, kwargs.pop(definition.name))
        super(TenantSpecificFieldsModelMixin, self).__init__(*args, **kwargs)

    def get_definitions(self, table_id=-1, force_hit_db=False):
        from shared_schema_tenants_custom_data.models import TenantSpecificFieldDefinition, TenantSpecificTable
        if not hasattr(self, 'definitions') or force_hit_db:
            if type(self).__name__ == 'TenantSpecificTableRow':
                self.definitions = TenantSpecificFieldDefinition.objects.filter(
                    table_content_type=ContentType.objects.get_for_model(TenantSpecificTable),
                    table_id=table_id)
            else:
                self.definitions = TenantSpecificFieldDefinition.objects.filter(
                    table_content_type=ContentType.objects.get_for_model(type(self)))
        return self.definitions

    def create_tenant_specific_fields(self, tenant_specific_fields_data):
        definitions = self.get_definitions()
        definitions_by_name = {d.name: d for d in definitions}

        with transaction.atomic():
            for field_name, definition in definitions_by_name.items():
                field_value = tenant_specific_fields_data.get(
                    field_name, getattr(self, field_name, None))
                PivotTableClass = _get_pivot_table_class_for_data_type(definition.data_type)
                PivotTableClass.objects.create(
                    definition=definition, row_id=self.id,
                    row_content_type=ContentType.objects.get_for_model(self.__class__),
                    value=field_value)

    def update_tenant_specific_fields(self, tenant_specific_fields_data):
        old = self.__class__.objects.get(pk=self.pk)
        definitions = self.get_definitions()
        definitions_by_name = {d.name: d for d in definitions}

        with transaction.atomic():
            for field_name, definition in definitions_by_name.items():
                new_value = tenant_specific_fields_data.get(field_name, None)
                old_value = getattr(old, field_name, None)
                PivotTableClass = _get_pivot_table_class_for_data_type(definition.data_type)
                if new_value != old_value:
                    PivotTableClass.objects.filter(
                        definition__id=definition.id, row_id=self.id,
                        row_content_type=ContentType.objects.get_for_model(self.__class__)
                    ).update(value=new_value)

    def save(self, *args, **kwargs):
        table_id = getattr(self, 'table_id', getattr(getattr(self, 'table', object()), 'id', None))

        force_hit_db = False
        if hasattr(self, 'definitions') and not self.definitions.exists():
            force_hit_db = True

        definitions = self.get_definitions(table_id=table_id, force_hit_db=force_hit_db)
        tenant_specific_fields_data = {}
        for definition in definitions:
            if hasattr(self, definition.name):
                tenant_specific_fields_data[definition.name] = getattr(self, definition.name)
                delattr(self, definition.name)
            else:
                tenant_specific_fields_data[definition.name] = definition.default_value

        if not self.pk:
            if not hasattr(self, 'tenant'):
                self.tenant = get_current_tenant()
            super(TenantSpecificFieldsModelMixin, self).save(*args, **kwargs)
            self.create_tenant_specific_fields(tenant_specific_fields_data)
        else:
            super(TenantSpecificFieldsModelMixin, self).save(*args, **kwargs)
            self.update_tenant_specific_fields(tenant_specific_fields_data)

        self.tenant_specific_fields_data = {}

    @property
    def fields_definitions(self):
        return self.get_definitions()

    class Meta:
        abstract = True


class TenantSpecificPivotTable(models.Model):
    definition = models.ForeignKey('TenantSpecificFieldDefinition')

    row_content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    row_id = models.PositiveIntegerField()
    row = GenericForeignKey(ct_field='row_content_type', fk_field='row_id')

    def __str__(self):
        return '%s: %s' % (str(self.definition), self.value)

    class Meta:
        unique_together = [('definition', 'row_id', 'row_content_type')]
        abstract = True
